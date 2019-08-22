#  Tencent is pleased to support the open source community by making GNES available.
#
#  Copyright (C) 2019 THL A29 Limited, a Tencent company. All rights reserved.
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.


import numpy as np
from typing import List

from ..base import BaseVideoPreprocessor
from ..helper import get_video_frames, compute_descriptor, compare_descriptor, detect_peak_boundary, compare_ecr
from ...proto import gnes_pb2, array2blob


class ShotDetectPreprocessor(BaseVideoPreprocessor):
    store_args_kwargs = True

    def __init__(self,
                 frame_size: str = '192*168',
                 descriptor: str = 'block_hsv_histogram',
                 distance_metric: str = 'bhattacharya',
                 detect_method: str = 'threshold',
                 frame_rate: str = '10',
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.frame_size = frame_size
        self.descriptor = descriptor
        self.distance_metric = distance_metric
        self.detect_method = detect_method
        self.frame_rate = frame_rate
        self._detector_kwargs = kwargs

    def detect_from_bytes(self, raw_bytes: bytes) -> (List[List['np.ndarray']], int):
        frames = get_video_frames(
            raw_bytes,
            s=self.frame_size,
            vsync='vfr',
            r=self.frame_rate)

        descriptors = []
        for frame in frames:
            descriptor = compute_descriptor(
                frame, method=self.descriptor, **self._detector_kwargs)
            descriptors.append(descriptor)

        # compute distances between frames
        if self.distance_metric == 'edge_change_ration':
            dists = compare_ecr(descriptors)
        else:
            dists = [
                compare_descriptor(pair[0], pair[1], self.distance_metric)
                for pair in zip(descriptors[:-1], descriptors[1:])
            ]

        shots = detect_peak_boundary(dists, self.detect_method)

        shot_frames = []
        for ci in range(0, len(shots) - 1):
            shot_frames.append(frames[shots[ci]:shots[ci+1]])

        return shot_frames, len(frames)

    def apply(self, doc: 'gnes_pb2.Document') -> None:
        super().apply(doc)
        #from sklearn.cluster import KMeans

        if doc.raw_bytes:
            shot_frames, num_frames = self.detect_from_bytes(doc.raw_bytes)

            for ci, value in enumerate(shot_frames):
                c = doc.chunks.add()
                c.doc_id = doc.doc_id
                chunk = np.array(value).astype('uint8')
                c.blob.CopyFrom(array2blob(chunk))
                c.offset_1d = ci
                c.weight = len(value) / num_frames
        else:
            self.logger.error('bad document: "raw_bytes" is empty!')

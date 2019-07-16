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

# pylint: disable=low-comment-ratio

import numpy as np
from .base import BaseVideoPreprocessor
from ...proto import gnes_pb2, array2blob
from ..helper import get_video_frames, compute_descriptor, compare_descriptor


class ShotDetectPreprocessor(BaseVideoPreprocessor):
    store_args_kwargs = True

    def __init__(self,
                 frame_size: str = "192*168",
                 descriptor: str = "block_hsv_histogram",
                 distance_metric: str = "bhattacharya",
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.frame_size = frame_size
        self.descriptor = descriptor
        self.distance_metric = distance_metric
        self._detector_kwargs = kwargs

    def apply(self, doc: 'gnes_pb2.Document') -> None:
        super().apply(doc)
        from sklearn.cluster import KMeans

        if doc.raw_bytes:
            # stream_data = io.BytesIO(doc.raw_bytes)
            # vidcap = cv2.VideoCapture(stream_data)
            frames = get_video_frames(
                doc.raw_bytes,
                s=self.frame_size,
                vsync="vfr",
                vf='select=eq(pict_type\\,I)')

            descriptors = []
            shots = []
            for frame in frames:
                descriptor = compute_descriptor(
                    frame, method=self.descriptor, **self._detector_kwargs)
                descriptors.append(descriptor)

            # compute distances between frames
            dists = [
                compare_descriptor(pair[0], pair[1], self.distance_metric)
                for pair in zip(descriptors[:-1], descriptors[1:])
            ]

            dists = np.array(dists).reshape([-1, 1])
            clt = KMeans(n_clusters=2)
            clt.fit(dists)

            #select which cluster includes shot frames
            big_center = np.argmax(clt.cluster_centers_)

            shots = []
            prev_shot = 0
            for i in range(0, len(clt.labels_)):
                if big_center == clt.labels_[i]:
                    shots.append((prev_shot, i + 2))
                    prev_shot = i + 2

            for ci, (start, end) in enumerate(shots):
                c = doc.chunks.add()
                c.doc_id = doc.doc_id
                chunk_pos = start + (end - start) // 2
                chunk = frames[chunk_pos]
                c.blob.CopyFrom(array2blob(chunk))
                c.offset_1d = ci
                c.weight = (end - start) / len(frames)

        else:
            self.logger.error('bad document: "raw_bytes" is empty!')

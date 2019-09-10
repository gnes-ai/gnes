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

import random
from typing import List

import numpy as np

from ..base import BaseVideoPreprocessor, RawChunkPreprocessor
from ..helper import split_video_frames, phash_descriptor
from ..io_utils import video as video_util
from ...proto import gnes_pb2, array2blob, blob2array


class FFmpegPreprocessor(BaseVideoPreprocessor):

    def __init__(self,
                 frame_size: str = '192:168',
                 frame_rate: int = 10,
                 frame_num: int = -1,
                 duplicate_rm: bool = True,
                 use_phash_weight: bool = False,
                 phash_thresh: int = 5,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.frame_size = frame_size
        self.frame_rate = frame_rate
        self.frame_num = frame_num
        self.phash_thresh = phash_thresh
        self.duplicate_rm = duplicate_rm
        self.use_phash_weight = use_phash_weight

    def apply(self, doc: 'gnes_pb2.Document') -> None:
        super().apply(doc)

        # video could't be processed from ndarray!
        # only bytes can be passed into ffmpeg pipeline
        if doc.raw_bytes:
            frames = video_util.capture_frames(input_data=doc.raw_bytes, scale=self.frame_size,
                                               fps=self.frame_rate, vframes=self.frame_num)
            # remove dupliated key frames by phash value
            if self.duplicate_rm:
                frames = self.duplicate_rm_hash(frames)

            if self.use_phash_weight:
                weight = FFmpegPreprocessor.pic_weight(frames)
            else:
                weight = [1 / len(frames)] * len(frames)

            for ci, chunk in enumerate(frames):
                c = doc.chunks.add()
                c.doc_id = doc.doc_id
                c.blob.CopyFrom(array2blob(chunk))
                c.offset = ci
                c.weight = weight[ci]

        else:
            self.logger.error('bad document: "raw_bytes" is empty!')

    @staticmethod
    def pic_weight(images: List['np.ndarray']) -> List[float]:
        import cv2
        weight = np.zeros([len(images)])
        # n_channel is usually 3 for RGB images
        n_channel = images[0].shape[-1]
        for i, image in enumerate(images):
            weight[i] = sum([
                cv2.calcHist([image], [_], None, [256], [0, 256]).var()
                for _ in range(n_channel)
            ])
        weight = weight / weight.sum()

        # normalized result
        weight = np.exp(-weight * 10)
        return weight / weight.sum()

    def duplicate_rm_hash(self,
                          images: List['np.ndarray']) -> List['np.ndarray']:
        hash_list = [phash_descriptor(_) for _ in images]
        ret = []
        for i, h in enumerate(hash_list):
            flag = 1
            if len(ret) >= 1:
                # only keep images with high phash diff
                # comparing only last kept 9 pics
                for j in range(1, min(len(ret) + 1, 9)):
                    dist = abs(ret[-j][1] - h)
                    if dist < self.phash_thresh:
                        flag = 0
                        break

            if flag:
                ret.append((i, h))

        return [images[_[0]] for _ in ret]


class FFmpegVideoSegmentor(BaseVideoPreprocessor):
    def __init__(self,
                 frame_size: str = '192:168',
                 frame_rate: int = 10,
                 frame_num: int = -1,
                 segment_method: str = 'cut_by_frame',
                 segment_interval: int = -1,
                 segment_num: int = 3,
                 max_frames_per_doc: int = -1,
                 use_image_input: bool = False,
                 splitter: str = '__split__',
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.frame_size = frame_size
        self.frame_rate = frame_rate
        self.frame_num = frame_num
        self.segment_method = segment_method
        self.segment_interval = segment_interval
        self.segment_num = segment_num
        self.max_frames_per_doc = max_frames_per_doc
        self.splitter = splitter
        self.use_image_input = use_image_input

    def apply(self, doc: 'gnes_pb2.Document') -> None:
        super().apply(doc)
        from sklearn.cluster import KMeans
        if doc.raw_bytes:
            if self.use_image_input:
                frames = split_video_frames(doc.raw_bytes, self.splitter)
            else:
                frames = video_util.capture_frames(input_data=doc.raw_bytes, scale=self.frame_size,
                                                   fps=self.frame_rate, vframes=self.frame_num)
            if self.max_frames_per_doc > 0:
                random_id = random.sample(range(len(frames)),
                                          k=min(self.max_frames_per_doc, len(frames)))
                frames = [frames[i] for i in sorted(random_id)]

            sub_videos = []
            if len(frames) >= 1:
                # cut by frame: should specify how many frames to cut
                if self.segment_method == 'cut_by_frame':
                    if self.segment_interval == -1:
                        sub_videos = [frames]
                    else:
                        sub_videos = [frames[_: _ + self.segment_interval]
                                      for _ in range(0, len(frames), self.segment_interval)]
                # cut by num: should specify how many chunks for each doc
                elif self.segment_method == 'cut_by_num':
                    if self.segment_num >= 2:
                        _interval = len(frames) // (self.segment_num - 1)
                        sub_videos = [frames[_: _ + _interval]
                                      for _ in range(0, len(frames), _interval)]
                    else:
                        sub_videos = [frames]

                # cut by clustering: params required
                #   segment_num
                elif self.segment_method == 'cut_by_clustering':
                    if self.segment_num >= 2:
                        hash_v = [phash_descriptor(_).hash for _ in frames]
                        hash_v = np.array(hash_v, dtype=np.int32).reshape([len(hash_v), -1])
                        label_v = KMeans(n_clusters=self.segment_num).fit_predict(hash_v)
                        sub_videos = [[frames[i] for i, j in enumerate(label_v) if j == _] for _ in
                                      range(self.segment_num)]
                    else:
                        sub_videos = [frames]

                for ci, chunk in enumerate(sub_videos):
                    c = doc.chunks.add()
                    c.doc_id = doc.doc_id
                    c.blob.CopyFrom(array2blob(np.array(chunk, dtype=np.uint8)))
                    c.offset = ci
                    c.weight = 1 / len(sub_videos)

            else:
                self.logger.warning('bad document: no key frames extracted')
        else:
            self.logger.error('bad document: "raw_bytes" is empty!')


class GifChunkPreprocessor(RawChunkPreprocessor, BaseVideoPreprocessor):
    @staticmethod
    def _parse_chunk(chunk: 'gnes_pb2.Chunk', *args, **kwargs):
        from ..io_utils import gif as gif_util

        return gif_util.encode_video(blob2array(chunk.blob), frame_rate=10)

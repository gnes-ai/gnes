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


import copy

import numpy as np

from ..base import BaseNumericEncoder
from ...helper import batching, train_required


class VladEncoder(BaseNumericEncoder):
    batch_size = 2048

    def __init__(self, num_clusters: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.num_clusters = num_clusters
        self.centroids = None

    def kmeans_train(self, vecs):
        import faiss

        kmeans = faiss.Kmeans(vecs.shape[1], self.num_clusters, niter=5, verbose=False)
        kmeans.train(vecs)
        self.centroids = kmeans.centroids

    def kmeans_pred(self, vecs):
        vecs = np.reshape(vecs, [vecs.shape[0], 1, 1, vecs.shape[1]])
        dist = np.sum(np.square(vecs - self.centroids), -1)
        return np.argmax(-dist, axis=-1).astype(np.int64)

    @batching
    def train(self, vecs: np.ndarray, *args, **kwargs):
        assert len(vecs) > self.num_clusters, 'number of data should be larger than number of clusters'
        vecs_ = copy.deepcopy(vecs)
        vecs_ = np.concatenate((list(vecs_[i] for i in range(len(vecs_)))), axis=0)
        self.kmeans_train(vecs_)

    @train_required
    @batching
    def encode(self, vecs: np.ndarray, *args, **kwargs) -> np.ndarray:
        vecs_ = copy.deepcopy(vecs)
        vecs_ = np.concatenate((list(vecs_[i] for i in range(len(vecs_)))), axis=0)

        knn_output = self.kmeans_pred(vecs_)
        knn_output = [knn_output[i:i + vecs.shape[1]] for i in range(0, len(knn_output), vecs.shape[1])]

        output = []
        for chunk_count, chunk in enumerate(vecs):
            res = np.zeros((self.centroids.shape[0], self.centroids.shape[1]))
            for frame_count, frame in enumerate(chunk):
                center_index = knn_output[chunk_count][frame_count][0]
                res[center_index] += (frame - self.centroids[center_index])
            output.append(res)

        output = np.array(list(map(lambda x: x.reshape(1, -1), output)), dtype=np.float32)
        output = np.squeeze(output, axis=1)
        return output

    def _copy_from(self, x: 'VladEncoder') -> None:
        self.num_clusters = x.num_clusters
        self.centroids = x.centroids

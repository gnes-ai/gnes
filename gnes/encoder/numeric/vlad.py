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

from ..base import BaseNumericEncoder
from ...helper import batching, train_required


class VladEncoder(BaseNumericEncoder):
    batch_size = 2048

    def __init__(self, num_clusters: int,
                 using_faiss_pred: bool = False,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.num_clusters = num_clusters
        self.using_faiss_pred = using_faiss_pred
        self.centroids = None
        self.index_flat = None

    def kmeans_train(self, vecs):
        import faiss
        kmeans = faiss.Kmeans(vecs.shape[1], self.num_clusters, niter=5, verbose=False)
        kmeans.train(vecs)
        self.centroids = kmeans.centroids
        self.centroids_l2 = np.sum(self.centroids**2, axis=1).reshape([1, -1])
        self.centroids_trans = np.transpose(self.centroids)
        if self.using_faiss_pred:
            self.faiss_index()

    def faiss_index(self):
        import faiss
        self.index_flat = faiss.IndexFlatL2(self.centroids.shape[1])
        self.index_flat.add(self.centroids)

    def kmeans_pred(self, vecs):
        if self.using_faiss_pred:
            _, pred = self.index_flat.search(vecs.astype(np.float32), 1)
            return np.reshape(pred, [-1])
        else:
            vecs_l2 = np.sum(vecs**2, axis=1).reshape([-1, 1])
            dist = vecs_l2 + self.centroids_l2 - 2 * np.matmul(vecs, self.centroids_trans)
            return np.argmax(dist, axis=-1).reshape([-1]).astype(np.int32)

    @batching
    def train(self, vecs: np.ndarray, *args, **kwargs):
        vecs = vecs.reshape([-1, vecs.shape[-1]])
        assert len(vecs) > self.num_clusters, 'number of data should be larger than number of clusters'
        self.kmeans_train(vecs)

    @train_required
    @batching
    def encode(self, vecs: np.ndarray, *args, **kwargs) -> np.ndarray:
        knn_output = [self.kmeans_pred(vecs_) for vecs_ in vecs]

        output = []
        for chunk_count, chunk in enumerate(vecs):
            res = np.zeros((self.centroids.shape[0], self.centroids.shape[1]))
            for frame_count, frame in enumerate(chunk):
                center_index = knn_output[chunk_count][frame_count]
                res[center_index] += (frame - self.centroids[center_index])
            res = res.reshape([-1])
            output.append(res / np.sum(res**2)**0.5)

        return np.array(output, dtype=np.float32)

    def _copy_from(self, x: 'VladEncoder') -> None:
        self.num_clusters = x.num_clusters
        self.centroids = x.centroids
        self.centroids_l2 = x.centroids_l2
        self.centroids_trans = np.transpose(self.centroids)
        self.using_faiss_pred = x.using_faiss_pred
        if self.using_faiss_pred:
            self.faiss_index()

    def __setstate__(self, state):
        super().__setstate__(state)
        if self.using_faiss_pred:
            self.faiss_index()

    def __getstate__(self):
        state = super().__getstate__()
        del state['index_flat']
        return state

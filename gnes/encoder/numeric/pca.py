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

from ..base import BaseNumericEncoder
from ...helper import get_perm, batching, get_optimal_sample_size, train_required


class PCALocalEncoder(BaseNumericEncoder):
    def __init__(self, output_dim: int, num_locals: int,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert output_dim >= num_locals and output_dim % num_locals == 0, \
            'output_dim should >= num_locals and can be divided by num_locals!'
        self.output_dim = output_dim
        self.num_locals = num_locals
        self.pca_components = None
        self.mean = None
        self.batch_size = 2048

    @batching(batch_size=get_optimal_sample_size, num_batch=1)
    def train(self, vecs: np.ndarray, *args, **kwargs) -> None:
        import faiss
        num_samples, num_dim = vecs.shape
        assert self.output_dim <= num_samples, 'training PCA requires at least %d points, but %d was given' % (
            self.output_dim, num_samples)
        assert self.output_dim < num_dim, 'PCA output dimension should < data dimension, received (%d, %d)' % (
            self.output_dim, num_dim)

        pca = faiss.PCAMatrix(num_dim, self.output_dim)
        self.mean = np.mean(vecs, axis=0)  # 1 x 768
        pca.train(vecs)
        explained_variance_ratio = faiss.vector_to_array(pca.eigenvalues)[:self.output_dim]
        components = faiss.vector_to_array(pca.PCAMat).reshape([-1, num_dim])[:self.output_dim]

        # permutate engive according to variance
        opt_order = get_perm(explained_variance_ratio, self.num_locals)
        comp_tmp = np.reshape(components[opt_order], [self.output_dim, num_dim])

        self.pca_components = np.transpose(comp_tmp)  # 768 x 200

    @train_required
    @batching
    def encode(self, vecs: np.ndarray, *args, **kwargs) -> np.ndarray:
        return np.matmul(vecs - self.mean, self.pca_components)

    def _copy_from(self, x: 'PCALocalEncoder') -> None:
        self.output_dim = x.output_dim
        self.pca_components = x.pca_components
        self.mean = x.mean
        self.num_locals = x.num_locals
        self.is_trained = x.is_trained

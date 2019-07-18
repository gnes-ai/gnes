import os
from typing import List, Tuple

import numpy as np

from ..base import BaseVectorIndexer
from ..key_only import ListKeyIndexer


class AnnoyIndexer(BaseVectorIndexer):

    def __init__(self, num_dim: int, data_path: str, metric: str = 'angular', n_trees=10, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.num_dim = num_dim
        self.data_path = data_path
        self.metric = metric
        self.n_trees = n_trees
        self._key_info_indexer = ListKeyIndexer()

    def post_init(self):
        from annoy import AnnoyIndex
        self._index = AnnoyIndex(self.num_dim, self.metric)
        try:
            if not os.path.exists(self.data_path):
                raise FileNotFoundError('"data_path" is not exist')
            if os.path.isdir(self.data_path):
                raise IsADirectoryError('"data_path" must be a file path, not a directory')
            self._index.load(self.data_path)
        except:
            self.logger.warning('fail to load model from %s, will create an empty one' % self.data_path)

    def add(self, keys: List[Tuple[int, int]], vectors: np.ndarray, weights: List[float], *args, **kwargs):
        last_idx = self._key_info_indexer.size

        if len(vectors) != len(keys):
            raise ValueError('vectors length should be equal to doc_ids')

        if vectors.dtype != np.float32:
            raise ValueError("vectors should be ndarray of float32")

        for idx, vec in enumerate(vectors):
            self._index.add_item(last_idx + idx, vec)

        self._key_info_indexer.add(keys, weights)

    def query(self, keys: 'np.ndarray', top_k: int, *args, **kwargs) -> List[List[Tuple]]:
        self._index.build(self.n_trees)
        if keys.dtype != np.float32:
            raise ValueError('vectors should be ndarray of float32')
        res = []
        for k in keys:
            ret, relevance_score = self._index.get_nns_by_vector(k, top_k, include_distances=True)
            chunk_info = self._key_info_indexer.query(ret)
            res.append([(*r, -s) for r, s in zip(chunk_info, relevance_score)])
        return res

    @property
    def size(self):
        return self._index.get_n_items()

    def __getstate__(self):
        d = super().__getstate__()
        self._index.save(self.data_path)
        return d

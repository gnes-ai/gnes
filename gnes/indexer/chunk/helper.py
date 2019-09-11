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


from typing import List, Tuple

import numpy as np

from ..base import BaseChunkIndexerHelper as CIH


class DictKeyIndexer(CIH):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._key_info = {}

    @CIH.update_counter
    def add(self, keys: List[Tuple[int, int]], weights: List[float], *args, **kwargs) -> int:
        for (k, o), w in zip(keys, weights):
            self._key_info[k] = o, w
        return len(self._key_info)

    def query(self, keys: List[int], *args, **kwargs) -> List[Tuple[int, int, float]]:
        return [(k, *self._key_info[k]) for k in keys]


class ListKeyIndexer(CIH):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._int2key = []  # type: List[Tuple[int, int]]
        self._int2key_weight = []  # type: List[float]

    @CIH.update_counter
    def add(self, keys: List[Tuple[int, int]], weights: List[float], *args, **kwargs) -> int:
        if len(keys) != len(weights):
            raise ValueError('"keys" and "weights" must have the same length')
        self._int2key.extend(keys)
        self._int2key_weight.extend(weights)
        return len(self._int2key)

    def query(self, keys: List[int], *args, **kwargs) -> List[Tuple[int, int, float]]:
        return [(*self._int2key[k], self._int2key_weight[k]) for k in keys]


class ListNumpyKeyIndexer(ListKeyIndexer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._data_updated = False
        self._np_int2key = None
        self._np_int2key_weight = None

    def _build_np_buffer(self):
        if self._data_updated or not self._np_int2key or not self._np_int2key_weight:
            self._np_int2key = np.array(self._int2key, int)
            self._np_int2key_weight = np.array(self._int2key_weight, float)

    def add(self, *args, **kwargs) -> int:
        self._data_updated = True
        return super().add(*args, **kwargs)

    def query(self, keys: List[int], *args, **kwargs) -> List[Tuple[int, int, float]]:
        self._build_np_buffer()
        key_offset = self._np_int2key[keys, 0:2].astype(int).tolist()
        weights = self._np_int2key_weight[keys].astype(float).tolist()
        return [(*ko, w) for ko, w in zip(key_offset, weights)]

    def __getstate__(self):
        d = super().__getstate__()
        del d['_np_int2key_weight']
        del d['_np_int2key']
        return d


class NumpyKeyIndexer(CIH):
    def __init__(self, buffer_size: int = 10000, col_size: int = 3, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._int2key_info = np.zeros([buffer_size, col_size])
        self._buffer_size = 10000
        self._col_size = col_size
        self._size = 0
        self._max_size = self._buffer_size
        self._all_docs = []

    @CIH.update_counter
    def add(self, keys: List[Tuple[int, int]], weights: List[float], *args, **kwargs) -> int:
        l = len(keys)
        if self._size + l > self._max_size:
            extend_size = max(l, self._buffer_size)
            self._int2key_info = np.concatenate([self._int2key_info, np.zeros([extend_size, self._col_size])])
            self._max_size += extend_size

        self._int2key_info[self._size:(self._size + l), 0:(self._col_size - 1)] = np.array(keys)
        self._int2key_info[self._size:(self._size + l), self._col_size - 1] = np.array(weights)
        self._size += l
        return self._size

    def query(self, keys: List[int], *args, **kwargs) -> List[Tuple[int, int, float]]:
        key_offset = self._int2key_info[keys, 0:(self._col_size - 1)].astype(int).tolist()
        weights = self._int2key_info[keys, self._col_size - 1].astype(float).tolist()
        return [(*ko, w) for ko, w in zip(key_offset, weights)]

    @property
    def capacity(self):
        return self._max_size

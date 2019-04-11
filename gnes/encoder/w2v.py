from typing import List
import numpy as np
import os
from joblib import Parallel, delayed
from .base import BaseEncoder
from ..helper import batching, cn_tokenizer


class W2vModel:
    def __init__(self, model_path: str, load_from_line: int):
        self.w2v = {}
        count = 0
        buff = []

        def trans(line):
            line = line.strip().split()
            try:
                res = (line[0], [float(_) for _ in line[1:]])
            except ValueError:
                res = (-1, -1)
            return res

        with open(model_path, 'r') as f:
            for line in f.readlines():
                if count < load_from_line:
                    continue
                else:
                    if len(buff) == 50000:
                        res = Parallel(n_jobs=20, verbose=0)(
                                delayed(trans)(line) for line in buff)
                        self.w2v.update(dict([i for i in res if i[0] != -1]))
                        buff = []
                    else:
                        buff.append(line)
        if len(buff) != 0:
            res = Parallel(n_jobs=20, verbose=0)(
                    delayed(trans)(line) for line in buff)
            self.w2v.update(dict(res))

    def encode(self, tokens):
        return [self.w2v[token] for token in tokens if token in self.w2v]


class W2vEncoder(BaseEncoder):
    def __init__(self, model_name: str = 'sgns.wiki.bigram-char',
                 load_from_line: int = 0,
                 batch_size: int = 64,
                 pooling_strategy: str = 'REDUCE_MEAN', *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model_name = model_name
        self.model_path = os.path.join('/', model_name)
        self.load_from_line = load_from_line
        self._w2v = W2vModel(self.model_path, self.load_from_line)

        self.batch_size = batch_size
        self.pooling_strategy = pooling_strategy

        self.is_trained = True

    @batching
    def encode(self, text: List[str], *args, **kwargs) -> np.ndarray:
        # tokenize text
        batch_tokens = [cn_tokenizer.tokenize(sent) for sent in text]
        pooled_data = []

        for tokens in batch_tokens:
            _layer_data = self._w2v.encode(tokens)
            if self.pooling_strategy is None or self.pooling_strategy == 'NONE':
                _pooled_data = _layer_data
            elif self.pooling_strategy == 'REDUCE_MEAN':
                _pooled_data = np.mean(_layer_data, 0)
            elif self.pooling_strategy == 'REDUCE_MAX':
                _pooled_data = np.max(_layer_data, 0)
            elif self.pooling_strategy == 'REDUCE_MEAN_MAX':
                _pooled_data = np.concatenate(
                    [np.mean(_layer_data, 0), np.max(_layer_data, 0)], 0)
            else:
                raise ValueError(
                    'pooling_strategy: %s has not been implemented' %
                    self.pooling_strategy)
            pooled_data.append(_pooled_data)
        return np.asarray(pooled_data, dtype=np.float32)

    def __getstate__(self):
        d = super().__getstate__()
        del d['_w2v']
        return d

    def __setstate__(self, d):
        super().__setstate__(d)
        self._w2v = W2vModel(self.model_path, self.load_from_line)

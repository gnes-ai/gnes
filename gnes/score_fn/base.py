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

import json
from typing import Sequence

import numpy as np

from ..base import TrainableBase
from ..proto import gnes_pb2


def get_unary_score(value: float, **kwargs):
    score = gnes_pb2.Response.QueryResponse.ScoredResult.Score()
    score.value = value
    score.explained = json.dumps(
        dict(value=float(value),
             **kwargs))
    return score


class BaseScoreFn(TrainableBase):
    """Base score function. A score function must implement __call__ method"""

    warn_unnamed = False

    def __init__(self, context=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._context = context

    def __call__(self, *args, **kwargs) -> 'gnes_pb2.Response.QueryResponse.ScoredResult.Score':
        raise NotImplementedError

    def new_score(self, *, operands: Sequence['gnes_pb2.Response.QueryResponse.ScoredResult.Score'] = (), **kwargs):
        if not self.__doc__:
            raise NotImplementedError('%s dont have docstring. For the sake of interpretability, '
                                      'please write docstring for this class')
        return get_unary_score(name=self.__class__.__name__,
                               docstring=' '.join(self.__doc__.split()).strip(),
                               operands=[json.loads(s.explained) for s in operands],
                               **kwargs)


class CombinedScoreFn(BaseScoreFn):
    """Combine multiple scores into one score, defaults to 'multiply'"""

    def __init__(self, score_mode: str = 'multiply', *args, **kwargs):
        """
        :param score_mode: specifies how the computed scores are combined
        """
        super().__init__(*args, **kwargs)
        if score_mode not in self.supported_ops:
            raise AttributeError(
                'score_mode=%s is not supported! must be one of %s' % (score_mode, self.supported_ops.keys()))
        self.score_mode = score_mode

    @property
    def supported_ops(self):
        return {
            'multiply': np.prod,
            'sum': np.sum,
            'max': np.max,
            'min': np.min,
            'avg': np.mean,
        }

    def post_init(self):
        self.op = self.supported_ops[self.score_mode]

    def __call__(self, *last_scores, **kwargs) -> 'gnes_pb2.Response.QueryResponse.ScoredResult.Score':
        return self.new_score(
            value=self.op([s.value for s in last_scores]),
            operands=last_scores,
            score_mode=self.score_mode)


class ModifierScoreFn(BaseScoreFn):
    """Modifier to apply to the value
    score = modifier(factor * value)
    """

    def __init__(self, modifier: str = 'none', factor: float = 1.0, factor_name: str = 'GivenConstant',
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        if modifier not in self.supported_ops:
            raise AttributeError(
                'modifier=%s is not supported! must be one of %s' % (modifier, self.supported_ops.keys()))
        self._modifier = modifier
        self._factor = factor
        self._factor_name = factor_name

    @property
    def supported_ops(self):
        return {
            'none': lambda x: x,
            'log': np.log10,
            'log1p': lambda x: np.log10(x + 1),
            'log2p': lambda x: np.log10(x + 2),
            'ln': np.log,
            'ln1p': np.log1p,
            'ln2p': lambda x: np.log(x + 2),
            'square': np.square,
            'sqrt': np.sqrt,
            'reciprocal': np.reciprocal,
            'reciprocal1p': lambda x: np.reciprocal(1 + x),
            'abs': np.abs,
            'invert': lambda x: - x,
            'invert1p': lambda x: 1 - x
        }

    def post_init(self):
        self.factor = get_unary_score(value=self._factor, name=self._factor_name)
        self.op = self.supported_ops[self._modifier]

    def __call__(self,
                 last_score: 'gnes_pb2.Response.QueryResponse.ScoredResult.Score',
                 *args, **kwargs) -> \
            'gnes_pb2.Response.QueryResponse.ScoredResult.Score':
        if self._modifier == 'none' and self._factor == 1.0:
            return last_score
        else:
            return self.new_score(
                value=self.op(self.factor.value * last_score.value),
                operands=[last_score],
                modifier=self._modifier,
                factor=json.loads(self.factor.explained))


class ScoreOps:
    multiply = CombinedScoreFn('multiply')
    sum = CombinedScoreFn('sum')
    max = CombinedScoreFn('max')
    min = CombinedScoreFn('min')
    avg = CombinedScoreFn('avg')
    none = ModifierScoreFn('none')
    log = ModifierScoreFn('log')
    log1p = ModifierScoreFn('log1p')
    log2p = ModifierScoreFn('log2p')
    ln = ModifierScoreFn('ln')
    ln1p = ModifierScoreFn('ln1p')
    ln2p = ModifierScoreFn('ln2p')
    square = ModifierScoreFn('square')
    sqrt = ModifierScoreFn('sqrt')
    abs = ModifierScoreFn('abs')
    reciprocal = ModifierScoreFn('reciprocal')
    reciprocal1p = ModifierScoreFn('reciprocal1p')

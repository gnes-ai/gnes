import json
from functools import reduce
from math import log, log1p, log10, sqrt
from operator import mul, add
from typing import Sequence

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
    unnamed_warning = False

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

    def op(self, *args, **kwargs) -> float:
        raise NotImplementedError


class ScoreCombinedFn(BaseScoreFn):
    """Combine multiple scores into one score, defaults to 'multiply'"""

    def __init__(self, score_mode: str = 'multiply', *args, **kwargs):
        """
        :param score_mode: specifies how the computed scores are combined
        """
        super().__init__(*args, **kwargs)
        if score_mode not in {'multiply', 'sum', 'avg', 'max', 'min'}:
            raise AttributeError('score_mode=%s is not supported!' % score_mode)
        self.score_mode = score_mode

    def __call__(self, *last_scores) -> 'gnes_pb2.Response.QueryResponse.ScoredResult.Score':
        return self.new_score(
            value=self.op(s.value for s in last_scores),
            operands=last_scores,
            score_mode=self.score_mode)

    def op(self, *args, **kwargs) -> float:
        return {
            'multiply': lambda v: reduce(mul, v),
            'sum': lambda v: reduce(add, v),
            'max': lambda v: reduce(max, v),
            'min': lambda v: reduce(min, v),
            'avg': lambda v: reduce(add, v) / len(v),
        }[self.score_mode](*args, **kwargs)


class ModifierFn(BaseScoreFn):
    """Modifier to apply to the value
    score = modifier(factor * value)
    """

    def __init__(self, modifier: str = 'none', factor: float = 1.0, factor_name: str = 'GivenConstant', *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        if modifier not in {'none', 'log', 'log1p', 'log2p', 'ln', 'ln1p', 'ln2p', 'square', 'sqrt', 'reciprocal',
                            'reciprocal1p', 'abs'}:
            raise AttributeError('modifier=%s is not supported!' % modifier)
        self._modifier = modifier
        self._factor = factor
        self._factor_name = factor_name

    @property
    def factor(self):
        return get_unary_score(value=self._factor, name=self._factor_name)

    def op(self, *args, **kwargs) -> float:
        return {
            'none': lambda x: x,
            'log': log10,
            'log1p': lambda x: log(x + 1, 10),
            'log2p': lambda x: log(x + 2, 10),
            'ln': log,
            'ln1p': log1p,
            'ln2p': lambda x: log(x + 2),
            'square': lambda x: x * x,
            'sqrt': sqrt,
            'reciprocal': lambda x: 1 / x,
            'reciprocal1p': lambda x: 1 / (1 + x),
            'abs': abs,
            'invert': lambda x: - x,
            'invert1p': lambda x: 1 - x
        }[self._modifier](*args, **kwargs)

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
    multiply = ScoreCombinedFn('multiply')
    sum = ScoreCombinedFn('sum')
    max = ScoreCombinedFn('max')
    min = ScoreCombinedFn('min')
    avg = ScoreCombinedFn('avg')
    none = ModifierFn('none')
    log = ModifierFn('log')
    log1p = ModifierFn('log1p')
    log2p = ModifierFn('log2p')
    ln = ModifierFn('ln')
    ln1p = ModifierFn('ln1p')
    ln2p = ModifierFn('ln2p')
    square = ModifierFn('square')
    sqrt = ModifierFn('sqrt')
    abs = ModifierFn('abs')
    reciprocal = ModifierFn('reciprocal')
    reciprocal1p = ModifierFn('reciprocal1p')

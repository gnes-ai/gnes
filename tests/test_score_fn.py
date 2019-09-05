import json
import unittest
from pprint import pprint

from gnes.proto import gnes_pb2
from gnes.score_fn.base import get_unary_score, CombinedScoreFn, ModifierScoreFn
from gnes.score_fn.chunk import WeightedChunkScoreFn
from gnes.score_fn.normalize import Normalizer1, Normalizer2, Normalizer3, Normalizer4


class TestScoreFn(unittest.TestCase):
    def test_basic(self):
        a = get_unary_score(0.5)
        b = get_unary_score(0.7)
        print(a)
        print(b.explained)

    def test_op(self):
        a = get_unary_score(0.5)
        b = get_unary_score(0.7)
        sum_op = CombinedScoreFn(score_mode='sum')
        c = sum_op(a, b)
        self.assertAlmostEqual(c.value, 1.2)

        sq_op = ModifierScoreFn(modifier='square')
        c = sum_op(a, sq_op(b))
        self.assertAlmostEqual(c.value, 0.99)
        print(c)

    def test_normalizer(self):
        a = get_unary_score(0.5)
        norm_op = Normalizer1()
        b = norm_op(a)
        pprint(json.loads(b.explained))

        a = get_unary_score(0.5)
        norm_op = Normalizer2(2)
        b = norm_op(a)
        pprint(json.loads(b.explained))
        self.assertAlmostEqual(b.value, 0.8)

        a = get_unary_score(0.5)
        norm_op = Normalizer3(2)
        b = norm_op(a)
        pprint(json.loads(b.explained))
        self.assertAlmostEqual(b.value, 0.7387961283389092)

        a = get_unary_score(0.5)
        norm_op = Normalizer4(2)
        b = norm_op(a)
        pprint(json.loads(b.explained))
        self.assertEqual(b.value, 0.75)

        norm_op = ModifierScoreFn('none')
        b = norm_op(a)
        pprint(json.loads(b.explained))
        self.assertEqual(b.value, 0.5)

        q_chunk = gnes_pb2.Chunk()
        q_chunk.weight = 0.5
        q_chunk.offset = 1
        d_chunk = gnes_pb2.Chunk()
        d_chunk.weight = 0.7
        d_chunk.offset = 2
        rel_score = get_unary_score(2)
        _op = WeightedChunkScoreFn()
        c = _op(rel_score, q_chunk, d_chunk)
        pprint(json.loads(c.explained))
        self.assertAlmostEqual(c.value, 0.7)

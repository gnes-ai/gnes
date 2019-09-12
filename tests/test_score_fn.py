import json
import unittest
from pprint import pprint

from gnes.proto import gnes_pb2
from gnes.score_fn.base import get_unary_score, CombinedScoreFn, ModifierScoreFn
from gnes.score_fn.chunk import WeightedChunkScoreFn, WeightedChunkOffsetScoreFn, CoordChunkScoreFn, TFIDFChunkScoreFn, BM25ChunkScoreFn
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

    def test_combine_score_fn(self):
        from gnes.indexer.chunk.helper import ListKeyIndexer
        from gnes.indexer.chunk.numpy import NumpyIndexer
        from gnes.proto import array2blob
        import numpy as np

        q_chunk = gnes_pb2.Chunk()
        q_chunk.doc_id = 2
        q_chunk.weight = 0.3
        q_chunk.offset = 0
        q_chunk.embedding.CopyFrom(array2blob(np.array([3, 3, 3])))

        for _fn in [WeightedChunkOffsetScoreFn, CoordChunkScoreFn, TFIDFChunkScoreFn, BM25ChunkScoreFn]:
            indexer = NumpyIndexer(helper_indexer=ListKeyIndexer(), score_fn=_fn())
            indexer.add(keys=[(0, 1), (1, 2)], vectors=np.array([[1, 1, 1], [2, 2, 2]]), weights=[0.5, 0.8])
            queried_result = indexer.query_and_score(q_chunks=[q_chunk], top_k=2)

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

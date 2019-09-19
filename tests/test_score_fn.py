import json
import unittest
from pprint import pprint

from gnes.proto import gnes_pb2
from gnes.score_fn.base import get_unary_score, CombinedScoreFn, ModifierScoreFn
from gnes.score_fn.chunk import WeightedChunkScoreFn, WeightedChunkOffsetScoreFn, CoordChunkScoreFn, TFIDFChunkScoreFn, BM25ChunkScoreFn
from gnes.score_fn.doc import CoordDocScoreFn
from gnes.score_fn.normalize import Normalizer1, Normalizer2, Normalizer3, Normalizer4

from gnes.cli.parser import set_router_parser, _set_client_parser
from gnes.service.base import SocketType
from gnes.client.base import ZmqClient
from gnes.service.router import RouterService


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

    def test_doc_combine_score_fn(self):
        from gnes.indexer.doc.dict import DictIndexer

        document_list = []
        document_id_list = []

        for j in range(1, 4):
            d = gnes_pb2.Document()
            for i in range(1, 4):
                c = d.chunks.add()
                c.doc_id = j
                c.offset = i
                c.weight = 1 / 3
            document_id_list.append(j)
            document_list.append(d)

        self.chunk_router_yaml = 'Chunk2DocTopkReducer'

        args = set_router_parser().parse_args([
            '--yaml_path', self.chunk_router_yaml,
            '--socket_out', str(SocketType.PUB_BIND)
        ])
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in),
            '--socket_in', str(SocketType.SUB_CONNECT)
        ])
        with RouterService(args), ZmqClient(c_args) as c1:
            msg = gnes_pb2.Message()
            s = msg.response.search.topk_results.add()
            s.score.value = 0.1
            s.score.explained = '"1-c1"'
            s.chunk.doc_id = 1

            s = msg.response.search.topk_results.add()
            s.score.value = 0.2
            s.score.explained = '"1-c2"'
            s.chunk.doc_id = 2

            s = msg.response.search.topk_results.add()

            s.score.value = 0.3
            s.score.explained = '"1-c3"'
            s.chunk.doc_id = 1

            msg.envelope.num_part.extend([1, 2])
            c1.send_message(msg)

            msg.response.search.ClearField('topk_results')

            s = msg.response.search.topk_results.add()
            s.score.value = 0.2
            s.score.explained = '"2-c1"'
            s.chunk.doc_id = 1

            s = msg.response.search.topk_results.add()
            s.score.value = 0.2
            s.score.explained = '"2-c2"'
            s.chunk.doc_id = 2

            s = msg.response.search.topk_results.add()
            s.score.value = 0.3
            s.score.explained = '"2-c3"'
            s.chunk.doc_id = 3
            c1.send_message(msg)
            r = c1.recv_message()
            doc_indexer = DictIndexer(score_fn=CoordDocScoreFn())
            doc_indexer.add(keys=document_id_list, docs=document_list)

            queried_result = doc_indexer.query_and_score(docs=r.response.search.topk_results, top_k=2)

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

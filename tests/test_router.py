import os
import unittest

import numpy as np

from gnes.cli.parser import set_router_service_parser, _set_client_parser
from gnes.proto import gnes_pb2, array2blob
from gnes.service.base import SocketType
from gnes.service.grpc import ZmqClient
from gnes.service.router import RouterService


class TestProto(unittest.TestCase):

    def setUp(self):
        self.dirname = os.path.dirname(__file__)
        self.publish_router_yaml = os.path.join(self.dirname, 'yaml', 'router-publish.yml')
        self.batch_router_yaml = os.path.join(self.dirname, 'yaml', 'router-batch.yml')
        self.reduce_router_yaml = os.path.join(self.dirname, 'yaml', 'router-reduce.yml')
        self.chunk_router_yaml = os.path.join(self.dirname, 'yaml', 'router-chunk-reduce.yml')
        self.doc_router_yaml = os.path.join(self.dirname, 'yaml', 'router-doc-reduce.yml')
        self.concat_router_yaml = os.path.join(self.dirname, 'yaml', 'router-concat.yml')

    def test_service_empty(self):
        args = set_router_service_parser().parse_args([])
        with RouterService(args):
            pass

    def test_map_router(self):
        args = set_router_service_parser().parse_args([
            '--yaml_path', self.batch_router_yaml,
        ])
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in),
        ])
        with RouterService(args), ZmqClient(c_args) as c1:
            msg = gnes_pb2.Message()
            msg.request.index.docs.extend([gnes_pb2.Document() for _ in range(5)])
            c1.send_message(msg)
            r = c1.recv_message()
            self.assertEqual(len(r.request.index.docs), 2)
            r = c1.recv_message()
            self.assertEqual(len(r.request.index.docs), 2)
            r = c1.recv_message()
            self.assertEqual(len(r.request.index.docs), 1)

    def test_publish_router(self):
        args = set_router_service_parser().parse_args([
            '--yaml_path', self.publish_router_yaml,
            '--socket_out', str(SocketType.PUB_BIND)
        ])
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in),
            '--socket_in', str(SocketType.SUB_CONNECT)
        ])
        with RouterService(args), ZmqClient(c_args) as c1, ZmqClient(c_args) as c2:
            msg = gnes_pb2.Message()
            msg.request.index.docs.extend([gnes_pb2.Document() for _ in range(5)])
            c1.send_message(msg)
            r = c1.recv_message()
            self.assertEqual(r.envelope.num_part, 2)
            r = c2.recv_message()
            self.assertEqual(r.envelope.num_part, 2)

    def test_reduce_router(self):
        args = set_router_service_parser().parse_args([
            '--yaml_path', self.reduce_router_yaml,
            '--socket_out', str(SocketType.PUB_BIND)
        ])
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in),
            '--socket_in', str(SocketType.SUB_CONNECT)
        ])
        with RouterService(args), ZmqClient(c_args) as c1, ZmqClient(c_args) as c2:
            msg = gnes_pb2.Message()
            msg.request.index.docs.extend([gnes_pb2.Document() for _ in range(5)])
            msg.envelope.num_part = 3
            c1.send_message(msg)
            c1.send_message(msg)
            c1.send_message(msg)
            r = c1.recv_message()
            self.assertEqual(r.envelope.num_part, 1)
            print(r.envelope.routes)

    def test_chunk_reduce_router(self):
        args = set_router_service_parser().parse_args([
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
            s.score = 0.1
            s.score_explained = '1-c1'
            s.chunk.doc_id = 1

            s = msg.response.search.topk_results.add()
            s.score = 0.2
            s.score_explained = '1-c2'
            s.chunk.doc_id = 2

            s = msg.response.search.topk_results.add()
            s.score = 0.3
            s.score_explained = '1-c3'
            s.chunk.doc_id = 1

            msg.envelope.num_part = 2
            c1.send_message(msg)

            msg.response.search.ClearField('topk_results')

            s = msg.response.search.topk_results.add()
            s.score = 0.2
            s.score_explained = '2-c1'
            s.chunk.doc_id = 1

            s = msg.response.search.topk_results.add()
            s.score = 0.2
            s.score_explained = '2-c2'
            s.chunk.doc_id = 2

            s = msg.response.search.topk_results.add()
            s.score = 0.3
            s.score_explained = '2-c3'
            s.chunk.doc_id = 3
            msg.envelope.num_part = 2
            c1.send_message(msg)
            r = c1.recv_message()
            self.assertEqual(r.envelope.num_part, 1)
            self.assertEqual(len(r.response.search.topk_results), 3)
            self.assertGreaterEqual(r.response.search.topk_results[0].score, r.response.search.topk_results[-1].score)
            print(r.response.search.topk_results)
            self.assertEqual(r.response.search.topk_results[0].score_explained, '1-c1\n1-c3\n2-c1\n')
            self.assertEqual(r.response.search.topk_results[1].score_explained, '1-c2\n2-c2\n')
            self.assertEqual(r.response.search.topk_results[2].score_explained, '2-c3\n')

            self.assertAlmostEqual(r.response.search.topk_results[0].score, 0.6)
            self.assertAlmostEqual(r.response.search.topk_results[1].score, 0.4)
            self.assertAlmostEqual(r.response.search.topk_results[2].score, 0.3)

    def test_doc_reduce_router(self):
        args = set_router_service_parser().parse_args([
            '--yaml_path', self.doc_router_yaml,
            '--socket_out', str(SocketType.PUB_BIND)
        ])
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in),
            '--socket_in', str(SocketType.SUB_CONNECT)
        ])
        with RouterService(args), ZmqClient(c_args) as c1:
            msg = gnes_pb2.Message()

            # shard1 only has d1
            s = msg.response.search.topk_results.add()
            s.score = 0.1
            s.doc.doc_id = 1
            s.doc.raw_text = 'd1'

            s = msg.response.search.topk_results.add()
            s.score = 0.2
            s.doc.doc_id = 2

            s = msg.response.search.topk_results.add()
            s.score = 0.3
            s.chunk.doc_id = 3

            msg.envelope.num_part = 2
            c1.send_message(msg)

            msg.response.search.ClearField('topk_results')

            # shard2 has d2 and d3
            s = msg.response.search.topk_results.add()
            s.score = 0.1
            s.doc.doc_id = 1

            s = msg.response.search.topk_results.add()
            s.score = 0.2
            s.doc.doc_id = 2
            s.doc.raw_text = 'd2'

            s = msg.response.search.topk_results.add()
            s.score = 0.3
            s.chunk.doc_id = 3
            s.doc.raw_text = 'd3'

            msg.response.search.top_k = 5
            msg.envelope.num_part = 2
            c1.send_message(msg)
            r = c1.recv_message()

            print(r.response.search.topk_results)
            self.assertEqual(r.envelope.num_part, 1)
            self.assertEqual(len(r.response.search.topk_results), 3)
            self.assertGreaterEqual(r.response.search.topk_results[0].score, r.response.search.topk_results[-1].score)

    def test_concat_router(self):
        args = set_router_service_parser().parse_args([
            '--yaml_path', self.concat_router_yaml,
            '--socket_out', str(SocketType.PUSH_BIND)
        ])
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in),
            '--socket_in', str(SocketType.PULL_CONNECT)
        ])
        with RouterService(args), ZmqClient(c_args) as c1:
            msg = gnes_pb2.Message()
            msg.request.search.query.chunk_embeddings.CopyFrom(array2blob(np.random.random([5, 2])))
            msg.envelope.num_part = 3
            c1.send_message(msg)
            c1.send_message(msg)
            c1.send_message(msg)
            r = c1.recv_message()
            self.assertEqual(r.envelope.num_part, 1)
            print(r.envelope.routes)
            self.assertEqual(r.request.search.query.chunk_embeddings.shape, [5, 6])

            for j in range(1, 4):
                d = msg.request.index.docs.add()
                d.chunk_embeddings.CopyFrom(array2blob(np.random.random([5, 2 * j])))

            msg.envelope.num_part = 3
            c1.send_message(msg)
            c1.send_message(msg)
            c1.send_message(msg)
            r = c1.recv_message()
            self.assertEqual(r.envelope.num_part, 1)
            for j in range(1, 4):
                self.assertEqual(r.request.index.docs[j - 1].chunk_embeddings.shape, [5, 6 * j])

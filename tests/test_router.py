import json
import os
import unittest

import numpy as np

from gnes.cli.parser import set_router_parser, _set_client_parser
from gnes.client.base import ZmqClient
from gnes.proto import gnes_pb2, array2blob
from gnes.service.base import SocketType
from gnes.service.router import RouterService


class TestProto(unittest.TestCase):

    def setUp(self):
        self.dirname = os.path.dirname(__file__)
        self.publish_router_yaml = '!PublishRouter {parameters: {num_part: 2}}'
        self.batch_router_yaml = '!DocBatchRouter {gnes_config: {batch_size: 2}}'
        self.reduce_router_yaml = 'BaseReduceRouter'
        self.chunk_router_yaml = 'Chunk2DocTopkReducer'
        self.chunk_sum_yaml = 'ChunkTopkReducer'
        self.doc_router_yaml = 'DocFillReducer'
        self.doc_sum_yaml = 'DocSumRouter'
        self.concat_router_yaml = 'ConcatEmbedRouter'
        self.avg_router_yaml = 'AvgEmbedRouter'

    def test_service_empty(self):
        args = set_router_parser().parse_args(['--yaml_path', 'BaseRouter'])
        with RouterService(args):
            pass

    def test_map_router(self):
        args = set_router_parser().parse_args([
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
        args = set_router_parser().parse_args([
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
            msg.envelope.num_part.append(1)
            c1.send_message(msg)
            r = c1.recv_message()
            self.assertSequenceEqual(r.envelope.num_part, [1, 2])
            r = c2.recv_message()
            self.assertSequenceEqual(r.envelope.num_part, [1, 2])

    def test_reduce_router(self):
        args = set_router_parser().parse_args([
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
            msg.envelope.num_part.extend([1, 3])
            c1.send_message(msg)
            c1.send_message(msg)
            c1.send_message(msg)
            r = c1.recv_message()
            self.assertSequenceEqual(r.envelope.num_part, [1])
            print(r.envelope.routes)

    def test_chunk_reduce_router(self):
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
            self.assertSequenceEqual(r.envelope.num_part, [1])
            self.assertEqual(len(r.response.search.topk_results), 3)
            self.assertGreaterEqual(r.response.search.topk_results[0].score.value,
                                    r.response.search.topk_results[-1].score.value)
            print(r.response.search.topk_results)
            self.assertEqual(json.loads(r.response.search.topk_results[0].score.explained)['operands'],
                             ['1-c1', '1-c3', '2-c1'])
            self.assertEqual(json.loads(r.response.search.topk_results[1].score.explained)['operands'],
                             ['1-c2', '2-c2'])
            self.assertEqual(json.loads(r.response.search.topk_results[2].score.explained)['operands'], ['2-c3'])

            self.assertAlmostEqual(r.response.search.topk_results[0].score.value, 0.6)
            self.assertAlmostEqual(r.response.search.topk_results[1].score.value, 0.4)
            self.assertAlmostEqual(r.response.search.topk_results[2].score.value, 0.3)

    def test_doc_reduce_router(self):
        args = set_router_parser().parse_args([
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
            s.score.value = 0.1
            s.doc.doc_id = 1
            s.doc.raw_text = 'd1'

            s = msg.response.search.topk_results.add()
            s.score.value = 0.2
            s.doc.doc_id = 2

            s = msg.response.search.topk_results.add()
            s.score.value = 0.3
            s.doc.doc_id = 3

            msg.envelope.num_part.extend([1, 2])
            c1.send_message(msg)

            msg.response.search.ClearField('topk_results')

            # shard2 has d2 and d3
            s = msg.response.search.topk_results.add()
            s.score.value = 0.1
            s.doc.doc_id = 1

            s = msg.response.search.topk_results.add()
            s.score.value = 0.2
            s.doc.doc_id = 2
            s.doc.raw_text = 'd2'

            s = msg.response.search.topk_results.add()
            s.score.value = 0.3
            s.doc.doc_id = 3
            s.doc.raw_text = 'd3'

            msg.response.search.top_k = 5
            c1.send_message(msg)
            r = c1.recv_message()

            print(r.response.search.topk_results)
            self.assertSequenceEqual(r.envelope.num_part, [1])
            self.assertEqual(len(r.response.search.topk_results), 3)

    @unittest.SkipTest
    def test_chunk_sum_reduce_router(self):
        args = set_router_parser().parse_args([
            '--yaml_path', self.chunk_sum_yaml,
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
            s.score.value = 0.6
            s.score.explained = json.dumps(['1-c1', '1-c3', '2-c1'])
            s.doc.doc_id = 1

            s = msg.response.search.topk_results.add()
            s.score.value = 0.4
            s.score.explained = json.dumps(['1-c2', '2-c2'])
            s.doc.doc_id = 2

            s = msg.response.search.topk_results.add()
            s.score.value = 0.3
            s.score.explained = json.dumps(['2-c3'])
            s.doc.doc_id = 3

            msg.envelope.num_part.extend([1, 2])
            c1.send_message(msg)

            msg.response.search.ClearField('topk_results')

            s = msg.response.search.topk_results.add()
            s.score.value = 0.5
            s.score.explained = json.dumps(['2-c1', '1-c2', '1-c1'])
            s.doc.doc_id = 2

            s = msg.response.search.topk_results.add()
            s.score.value = 0.3
            s.score.explained = json.dumps(['1-c3', '2-c2'])
            s.doc.doc_id = 3

            s = msg.response.search.topk_results.add()
            s.score.value = 0.1
            s.score.explained = json.dumps(['2-c3'])
            s.doc.doc_id = 1
            c1.send_message(msg)
            r = c1.recv_message()
            self.assertSequenceEqual(r.envelope.num_part, [1])
            self.assertEqual(len(r.response.search.topk_results), 3)
            self.assertGreaterEqual(r.response.search.topk_results[0].score.value,
                                    r.response.search.topk_results[-1].score.value)
            print(r.response.search.topk_results)
            self.assertEqual(r.response.search.topk_results[0].score.explained, '1-c2\n2-c2\n\n2-c1\n1-c2\n1-c1\n\n')
            self.assertEqual(r.response.search.topk_results[1].score.explained, '1-c1\n1-c3\n2-c1\n\n2-c3\n\n')
            self.assertEqual(r.response.search.topk_results[2].score.explained, '2-c3\n\n1-c3\n2-c2\n\n')

            self.assertAlmostEqual(r.response.search.topk_results[0].score.value, 0.9)
            self.assertAlmostEqual(r.response.search.topk_results[1].score.value, 0.7)
            self.assertAlmostEqual(r.response.search.topk_results[2].score.value, 0.6)

    @unittest.SkipTest
    def test_doc_sum_reduce_router(self):
        args = set_router_parser().parse_args([
            '--yaml_path', self.doc_sum_yaml,
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
            s.score.value = 0.4
            s.doc.doc_id = 1
            s.doc.raw_text = 'd3'
            s.score.explained = '1-d3\n'

            s = msg.response.search.topk_results.add()
            s.score.value = 0.3
            s.doc.doc_id = 2
            s.doc.raw_text = 'd2'
            s.score.explained = '1-d2\n'

            s = msg.response.search.topk_results.add()
            s.score.value = 0.2
            s.doc.doc_id = 3
            s.doc.raw_text = 'd1'
            s.score.explained = '1-d3\n'

            msg.envelope.num_part.extend([1, 2])
            c1.send_message(msg)

            msg.response.search.ClearField('topk_results')

            s = msg.response.search.topk_results.add()
            s.score.value = 0.5
            s.doc.doc_id = 1
            s.doc.raw_text = 'd2'
            s.score.explained = '2-d2\n'

            s = msg.response.search.topk_results.add()
            s.score.value = 0.2
            s.doc.doc_id = 2
            s.doc.raw_text = 'd1'
            s.score.explained = '2-d1\n'

            s = msg.response.search.topk_results.add()
            s.score.value = 0.1
            s.doc.doc_id = 3
            s.doc.raw_text = 'd3'
            s.score.explained = '2-d3\n'

            msg.response.search.top_k = 5
            c1.send_message(msg)
            r = c1.recv_message()

            print(r.response.search.topk_results)
            self.assertSequenceEqual(r.envelope.num_part, [1])
            self.assertEqual(len(r.response.search.topk_results), 3)
            self.assertGreaterEqual(r.response.search.topk_results[0].score.value,
                                    r.response.search.topk_results[-1].score.value)

    # @unittest.SkipTest
    def test_concat_router(self):
        args = set_router_parser().parse_args([
            '--yaml_path', self.concat_router_yaml,
            '--socket_out', str(SocketType.PUSH_BIND)
        ])
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in),
            '--socket_in', str(SocketType.PULL_CONNECT)
        ])
        # 10 chunks in each doc, dimension of chunk embedding is (5, 2)
        with RouterService(args), ZmqClient(c_args) as c1:
            msg = gnes_pb2.Message()
            for i in range(10):
                c = msg.request.search.query.chunks.add()
                c.embedding.CopyFrom(array2blob(np.random.random([5, 2])))
            msg.envelope.num_part.extend([1, 3])
            c1.send_message(msg)
            c1.send_message(msg)
            c1.send_message(msg)
            r = c1.recv_message()
            self.assertSequenceEqual(r.envelope.num_part, [1])
            print(r.envelope.routes)
            for i in range(10):
                self.assertEqual(r.request.search.query.chunks[i].embedding.shape, [5, 6])

            for j in range(1, 4):
                d = msg.request.index.docs.add()
                for k in range(10):
                    c = d.chunks.add()
                    c.embedding.CopyFrom(array2blob(np.random.random([5, 2])))

            c1.send_message(msg)
            c1.send_message(msg)
            c1.send_message(msg)
            r = c1.recv_message()
            self.assertSequenceEqual(r.envelope.num_part, [1])
            for j in range(1, 4):
                for i in range(10):
                    self.assertEqual(r.request.index.docs[j - 1].chunks[i].embedding.shape, [5, 6])
    
    def test_avg_router(self):
        args = set_router_parser().parse_args([
            '--yaml_path', self.avg_router_yaml,
            '--socket_out', str(SocketType.PUSH_BIND)
        ])
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in),
            '--socket_in', str(SocketType.PULL_CONNECT)
        ])
        # 10 chunks in each doc, dimension of chunk embedding is (5, 2)
        with RouterService(args), ZmqClient(c_args) as c1:
            msg = gnes_pb2.Message()
            for i in range(10):
                c = msg.request.search.query.chunks.add()
                c.embedding.CopyFrom(array2blob(np.random.random([5, 2])))
            msg.envelope.num_part.extend([1, 3])
            c1.send_message(msg)
            c1.send_message(msg)
            c1.send_message(msg)
            r = c1.recv_message()
            self.assertSequenceEqual(r.envelope.num_part, [1])
            print(r.envelope.routes)
            for i in range(10):
                self.assertEqual(r.request.search.query.chunks[i].embedding.shape, [5, 2])

            for j in range(1, 4):
                d = msg.request.index.docs.add()
                for k in range(10):
                    c = d.chunks.add()
                    c.embedding.CopyFrom(array2blob(np.random.random([5, 2])))

            c1.send_message(msg)
            c1.send_message(msg)
            c1.send_message(msg)
            r = c1.recv_message()
            self.assertSequenceEqual(r.envelope.num_part, [1])
            for j in range(1, 4):
                for i in range(10):
                    self.assertEqual(r.request.index.docs[j - 1].chunks[i].embedding.shape, [5, 2])
                    
    def test_multimap_multireduce(self):
        # p1 ->
        #      p21 ->
        #              r311
        #              r312
        #                   ->  r41
        #                             -> r5
        #      p22 ->
        #              r321
        #              r322
        #                   -> r42
        #                             -> r5
        #                                       -> client
        p1 = set_router_parser().parse_args([
            '--yaml_path', self.publish_router_yaml,
            '--socket_in', str(SocketType.PULL_CONNECT),
            '--socket_out', str(SocketType.PUB_BIND),
        ])
        r5 = set_router_parser().parse_args([
            '--yaml_path', self.reduce_router_yaml,
            '--socket_in', str(SocketType.PULL_BIND),
            '--socket_out', str(SocketType.PUSH_CONNECT),
        ])
        r41 = set_router_parser().parse_args([
            '--yaml_path', self.reduce_router_yaml,
            '--socket_in', str(SocketType.PULL_BIND),
            '--socket_out', str(SocketType.PUSH_CONNECT),
            '--port_out', str(r5.port_in)
        ])
        r42 = set_router_parser().parse_args([
            '--yaml_path', self.reduce_router_yaml,
            '--socket_in', str(SocketType.PULL_BIND),
            '--socket_out', str(SocketType.PUSH_CONNECT),
            '--port_out', str(r5.port_in)
        ])
        p21 = set_router_parser().parse_args([
            '--yaml_path', self.publish_router_yaml,
            '--socket_in', str(SocketType.SUB_CONNECT),
            '--socket_out', str(SocketType.PUB_BIND),
            '--port_in', str(p1.port_out),
            '--identity', ''
        ])
        p22 = set_router_parser().parse_args([
            '--yaml_path', self.publish_router_yaml,
            '--socket_in', str(SocketType.SUB_CONNECT),
            '--socket_out', str(SocketType.PUB_BIND),
            '--port_in', str(p1.port_out),
            '--identity', ''
        ])
        r311 = set_router_parser().parse_args([
            '--socket_in', str(SocketType.SUB_CONNECT),
            '--socket_out', str(SocketType.PUSH_CONNECT),
            '--port_in', str(p21.port_out),
            '--port_out', str(r41.port_in),
            '--yaml_path', 'BaseRouter',
            '--identity', ''
        ])
        r312 = set_router_parser().parse_args([
            '--socket_in', str(SocketType.SUB_CONNECT),
            '--socket_out', str(SocketType.PUSH_CONNECT),
            '--port_in', str(p21.port_out),
            '--port_out', str(r41.port_in),
            '--yaml_path', 'BaseRouter',
            '--identity', ''
        ])
        r321 = set_router_parser().parse_args([
            '--socket_in', str(SocketType.SUB_CONNECT),
            '--socket_out', str(SocketType.PUSH_CONNECT),
            '--port_in', str(p22.port_out),
            '--port_out', str(r42.port_in),
            '--yaml_path', 'BaseRouter',
            '--identity', ''
        ])
        r322 = set_router_parser().parse_args([
            '--socket_in', str(SocketType.SUB_CONNECT),
            '--socket_out', str(SocketType.PUSH_CONNECT),
            '--port_in', str(p22.port_out),
            '--port_out', str(r42.port_in),
            '--yaml_path', 'BaseRouter',
            '--identity', ''
        ])

        c_args = _set_client_parser().parse_args([
            '--port_in', str(r5.port_out),
            '--port_out', str(p1.port_in),
            '--socket_in', str(SocketType.PULL_BIND),
            '--socket_out', str(SocketType.PUSH_BIND),
        ])
        with RouterService(p1), RouterService(r5), \
             RouterService(p21), RouterService(p22), \
             RouterService(r311), RouterService(r312), RouterService(r321), RouterService(r322), \
             RouterService(r41), RouterService(r42), \
             ZmqClient(c_args) as c1:
            msg = gnes_pb2.Message()
            msg.envelope.num_part.append(1)
            c1.send_message(msg)
            r = c1.recv_message()
            self.assertSequenceEqual(r.envelope.num_part, [1])
            print(r.envelope.routes)

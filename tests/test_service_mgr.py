import os
import unittest.mock

import grpc

from gnes.cli.parser import set_router_service_parser, set_frontend_parser
from gnes.proto import gnes_pb2_grpc, RequestGenerator
from gnes.service.base import ServiceManager, SocketType, ParallelType
from gnes.service.frontend import FrontendService
from gnes.service.router import RouterService


class TestServiceManager(unittest.TestCase):
    def setUp(self):
        self.all_bytes = [b'abc', b'def', b'cde'] * 10
        self.all_bytes2 = [b'abc', b'def', b'cde']
        os.unsetenv('http_proxy')
        os.unsetenv('https_proxy')

    def _test_multiple_router(self, backend='thread', num_parallel=5):
        a = set_router_service_parser().parse_args([
            '--yaml_path', 'BaseRouter',
            '--num_parallel', str(num_parallel),
            '--parallel_backend', backend
        ])
        with ServiceManager(RouterService, a):
            pass

    def _test_grpc_multiple_router(self, backend='thread', num_parallel=5):
        args = set_frontend_parser().parse_args([
            '--grpc_host', '127.0.0.1',
        ])

        p_args = set_router_service_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in),
            '--socket_in', str(SocketType.PULL_CONNECT),
            '--socket_out', str(SocketType.PUSH_CONNECT),
            '--yaml_path', 'BaseRouter',
            '--num_parallel', str(num_parallel),
            '--parallel_backend', backend
        ])

        with ServiceManager(RouterService, p_args), FrontendService(args), grpc.insecure_channel(
                '%s:%s' % (args.grpc_host, args.grpc_port),
                options=[('grpc.max_send_message_length', 70 * 1024 * 1024),
                         ('grpc.max_receive_message_length', 70 * 1024 * 1024)]) as channel:
            stub = gnes_pb2_grpc.GnesRPCStub(channel)
            resp = stub.Call(list(RequestGenerator.query(b'abc', 1))[0])
            self.assertEqual(resp.request_id, '0')

    def _test_grpc_multiple_pub(self, backend='thread', num_parallel=5):
        args = set_frontend_parser().parse_args([
            '--grpc_host', '127.0.0.1',
        ])

        p_args = set_router_service_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in),
            '--socket_in', str(SocketType.PULL_CONNECT),
            '--socket_out', str(SocketType.PUSH_CONNECT),
            '--yaml_path', 'BaseRouter',
            '--num_parallel', str(num_parallel),
            '--parallel_backend', backend,
            '--parallel_type', str(ParallelType.PUB_BLOCK)
        ])

        with ServiceManager(RouterService, p_args), FrontendService(args), grpc.insecure_channel(
                '%s:%s' % (args.grpc_host, args.grpc_port),
                options=[('grpc.max_send_message_length', 70 * 1024 * 1024),
                         ('grpc.max_receive_message_length', 70 * 1024 * 1024)]) as channel:
            stub = gnes_pb2_grpc.GnesRPCStub(channel)
            resp = stub.Call(list(RequestGenerator.query(b'abc', 1))[0])
            self.assertEqual(resp.request_id, '0')

    def test_grpc_with_pub(self):
        self._test_grpc_multiple_pub('thread', 1)
        self._test_grpc_multiple_pub('process', 1)
        self._test_grpc_multiple_pub('thread', 5)
        self._test_grpc_multiple_pub('process', 5)

    def test_grpc_with_multi_service(self):
        self._test_grpc_multiple_router('thread', 1)
        self._test_grpc_multiple_router('process', 1)
        self._test_grpc_multiple_router('thread', 5)
        self._test_grpc_multiple_router('process', 5)

    def test_multiple_router(self):
        self._test_multiple_router('thread', 1)
        self._test_multiple_router('process', 1)
        self._test_multiple_router('thread', 5)
        self._test_multiple_router('process', 5)

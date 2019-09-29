import os
import time
import unittest.mock

import grpc

from gnes.cli.parser import set_frontend_parser, set_router_parser
from gnes.helper import TimeContext
from gnes.proto import RequestGenerator, gnes_pb2_grpc
from gnes.service.base import SocketType, MessageHandler, BaseService as BS
from gnes.service.frontend import FrontendService
from gnes.service.router import RouterService


class Router1(RouterService):
    handler = MessageHandler(BS.handler)

    @handler.register(NotImplementedError)
    def _handler_default(self, msg: 'gnes_pb2.Message'):
        self.logger.info('im doing fancy jobs...')
        time.sleep(2)
        super()._handler_default(msg)


class Router2(RouterService):
    handler = MessageHandler(BS.handler)

    @handler.register(NotImplementedError)
    def _handler_default(self, msg: 'gnes_pb2.Message'):
        self.logger.info('im doing stupid jobs...')
        time.sleep(6)
        super()._handler_default(msg)


class TestStreamgRPC(unittest.TestCase):

    def setUp(self):
        self.all_bytes = [b'abc', b'def', b'cde'] * 10
        self.all_bytes2 = [b'abc', b'def', b'cde']
        os.unsetenv('http_proxy')
        os.unsetenv('https_proxy')

    def test_bm_frontend(self):
        args = set_frontend_parser().parse_args([
            '--grpc_host', '127.0.0.1',

        ])

        p_args = set_router_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in),
            '--socket_in', str(SocketType.PULL_CONNECT),
            '--socket_out', str(SocketType.PUSH_CONNECT),
            '--yaml_path', 'BaseRouter'
        ])

    def test_grpc_frontend(self):
        args = set_frontend_parser().parse_args([
            '--grpc_host', '127.0.0.1',

        ])

        p_args = set_router_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in),
            '--socket_in', str(SocketType.PULL_CONNECT),
            '--socket_out', str(SocketType.PUSH_CONNECT),
            '--yaml_path', 'BaseRouter'
        ])

        with RouterService(p_args), FrontendService(args), grpc.insecure_channel(
                '%s:%d' % (args.grpc_host, args.grpc_port),
                options=[('grpc.max_send_message_length', 70 * 1024 * 1024),
                         ('grpc.max_receive_message_length', 70 * 1024 * 1024)]) as channel:
            stub = gnes_pb2_grpc.GnesRPCStub(channel)
            with TimeContext('sync call'):  # about 5s
                resp = list(stub.StreamCall(RequestGenerator.train(self.all_bytes, batch_size=1)))[-1]

            self.assertEqual(resp.request_id, len(self.all_bytes))  # idx start with 0, but +1 for final FLUSH

    def test_async_block(self):
        args = set_frontend_parser().parse_args([
            '--grpc_host', '127.0.0.1',
        ])

        p1_args = set_router_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', '8899',
            '--socket_in', str(SocketType.PULL_CONNECT),
            '--socket_out', str(SocketType.PUSH_CONNECT),
            '--yaml_path', 'BaseRouter'
        ])

        p2_args = set_router_parser().parse_args([
            '--port_in', str(p1_args.port_out),
            '--port_out', str(args.port_in),
            '--socket_in', str(SocketType.PULL_BIND),
            '--socket_out', str(SocketType.PUSH_CONNECT),
            '--yaml_path', 'BaseRouter'
        ])

        with FrontendService(args), Router1(p1_args), Router2(p2_args), grpc.insecure_channel(
                '%s:%d' % (args.grpc_host, args.grpc_port),
                options=[('grpc.max_send_message_length', 70 * 1024 * 1024),
                         ('grpc.max_receive_message_length', 70 * 1024 * 1024)]) as channel:
            stub = gnes_pb2_grpc.GnesRPCStub(channel)
            id = 0
            with TimeContext('non-blocking call'):  # about 26s = 32s (total) - 3*2s (overlap)
                resp = stub.StreamCall(RequestGenerator.train(self.all_bytes2, batch_size=1))
                for r in resp:
                    self.assertEqual(r.request_id, id)
                    id += 1

            id = 0
            with TimeContext('blocking call'):  # should be 32 s
                for r in RequestGenerator.train(self.all_bytes2, batch_size=1):
                    resp = stub.Call(r)
                    self.assertEqual(resp.request_id, id)
                    id += 1
            # self.assertEqual(resp.result().request_id, str(len(self.all_bytes)))

            # self.assertEqual(resp.request_id, str(len(self.all_bytes2)))  # idx start with 0, but +1 for final FLUSH

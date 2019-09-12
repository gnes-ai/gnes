import os
import unittest
from concurrent.futures import ThreadPoolExecutor

import grpc

from gnes.cli.parser import set_grpc_service_parser, set_frontend_parser
from gnes.proto import gnes_pb2_grpc, RequestGenerator
from gnes.service.frontend import FrontendService
from gnes.service.grpc import GRPCService
from tests.proto_s import dummy_pb2_grpc


class DummyServer:
    def __init__(self, bind_address):
        self.server = grpc.server(
            ThreadPoolExecutor(max_workers=1),
            options=[('grpc.max_send_message_length', 1 * 1024 * 1024),
                     ('grpc.max_receive_message_length', 1 * 1024 * 1024)])
        dummy_pb2_grpc.add_DummyGRPCServiceServicer_to_server(self.GNESServicer(), self.server)
        self.bind_address = bind_address
        self.server.add_insecure_port(self.bind_address)

    def __enter__(self):
        self.server.start()
        print('dummy server is listening at: %s' % self.bind_address)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.server.stop(None)

    class GNESServicer(dummy_pb2_grpc.DummyGRPCServiceServicer):

        def dummyAPI(self, request, context):
            print('the dummy server received something: %s' % request)
            return request


class TestGRPCService(unittest.TestCase):
    def setUp(self):
        os.unsetenv('http_proxy')
        os.unsetenv('https_proxy')
        self.dirname = os.path.dirname(__file__)

        self.s_args = set_grpc_service_parser().parse_args([
            '--grpc_port', '5678',
            '--grpc_host', '127.0.0.1',
            '--pb2_path', os.path.join(self.dirname, 'proto', 'dummy_pb2.py'),
            '--pb2_grpc_path', os.path.join(self.dirname, 'proto', 'dummy_pb2_grpc.py'),
            '--stub_name', 'DummyGRPCServiceStub',
            '--api_name', 'dummyAPI'
        ])

        self.args = set_frontend_parser().parse_args([
            '--grpc_host', '127.0.0.1',
            '--grpc_port', '9999',
            '--port_in', str(self.s_args.port_out),
            '--port_out', str(self.s_args.port_in),

        ])

    def test_grpc_empty_service(self):
        with DummyServer('%s:%d' % (self.s_args.grpc_host, self.s_args.grpc_port)), GRPCService(self.s_args):
            pass

    @unittest.SkipTest
    def test_grpc_real_service(self):
        # to fix

        with DummyServer('%s:%d' % (self.s_args.grpc_host, self.s_args.grpc_port)), GRPCService(
                self.s_args), FrontendService(self.args), grpc.insecure_channel(
            '%s:%s' % (self.args.grpc_host, self.args.grpc_port),
            options=[('grpc.max_send_message_length', 70 * 1024 * 1024),
                     ('grpc.max_receive_message_length', 70 * 1024 * 1024)]) as channel:
            stub = gnes_pb2_grpc.GnesRPCStub(channel)
            resp = stub.Call(list(RequestGenerator.query(b'abc', 1))[0])
            self.assertEqual(resp.request_id, 0)  # idx start with 0, but +1 for final FLUSH

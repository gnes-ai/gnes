import threading
import unittest

import grpc

from gnes.cli.parser import set_grpc_frontend_parser, set_proxy_service_parser
from gnes.proto import gnes_pb2, gnes_pb2_grpc
from gnes.service.grpc import GRPCFrontend
from gnes.service.proxy import ProxyService


class TestGRPCService(unittest.TestCase):

    def test_grpc(self):
        # https://github.com/grpc/grpc/issues/9987#issuecomment-370156099
        p_args = set_proxy_service_parser().parse_args([
            '--socket_in',
            'PULL_BIND',
            '--socket_out',
            'PUSH_BIND',
        ])
        g_args = set_grpc_frontend_parser().parse_args([])
        with ProxyService(p_args), GRPCFrontend(g_args):
            with grpc.insecure_channel(
                    '%s:%s' % ('127.0.0.1', g_args.grpc_port),
                    options=[('grpc.max_send_message_length', 50 * 1024 * 1024),
                             ('grpc.max_receive_message_length', 50 * 1024 * 1024)]) as channel:
                stub = gnes_pb2_grpc.GnesRPCStub(channel)
                r = gnes_pb2.Request()
                p = stub._Call(r)
                print(p)


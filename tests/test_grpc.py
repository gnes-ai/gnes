import os
import unittest

from gnes.cli.parser import set_proxy_service_parser, set_grpc_service_parser
from gnes.service import proxy, grpc

class TestGRPCService(unittest.TestCase):

    def test_grpc_service(self):
        m_args = set_proxy_service_parser().parse_args([
            '--port_in',
            '1111',
            '--port_out',
            '1112',
            '--socket_in',
            'PULL_BIND',
            '--socket_out',
            'PUB_BIND',
        ])
        g_args = set_grpc_service_parser().parse_args([
            '--port_in',
            str(m_args.port_out),
            '--port_out',
            str(m_args.port_in)
        ])

        with proxy.ProxyService(m_args):
            grpc.start_serve(g_args)
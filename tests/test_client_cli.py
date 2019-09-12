import os
import unittest

from gnes.cli.parser import set_frontend_parser, set_router_parser, set_client_cli_parser
from gnes.client.cli import CLIClient
from gnes.service.base import SocketType
from gnes.service.frontend import FrontendService
from gnes.service.router import RouterService


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.dirname = os.path.dirname(__file__)
        os.unsetenv('http_proxy')
        os.unsetenv('https_proxy')

    def test_cli(self):
        cli_args = set_client_cli_parser().parse_args([
            '--mode', 'train',
            '--grpc_host', '127.0.0.1',
            '--txt_file', os.path.join(self.dirname, 'sonnets.txt')
        ])

        args = set_frontend_parser().parse_args([

        ])

        p_args = set_router_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in),
            '--socket_in', str(SocketType.PULL_CONNECT),
            '--socket_out', str(SocketType.PUSH_CONNECT),
            '--host_in', '127.0.0.1',
            '--host_out', '127.0.0.1',
            '--yaml_path', 'BaseRouter'
        ])

        with RouterService(p_args), FrontendService(args) as s:
            CLIClient(cli_args)



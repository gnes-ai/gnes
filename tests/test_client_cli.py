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
        self.test_file = os.path.join(self.dirname, 'sonnets_small.txt')
        self.train_args = set_client_cli_parser().parse_args([
            '--mode', 'train',
            '--txt_file', self.test_file,
            '--batch_size', '4'
        ])
        self.index_args = set_client_cli_parser().parse_args([
            '--mode', 'index',
            '--txt_file', self.test_file,
            '--batch_size', '4'
        ])
        self.query_args = set_client_cli_parser().parse_args([
            '--mode', 'query',
            '--txt_file', self.test_file,
            '--batch_size', '4'
        ])
        os.unsetenv('http_proxy')
        os.unsetenv('https_proxy')

    def test_cli(self):
        args = set_frontend_parser().parse_args([])

        p_args = set_router_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in),
            '--socket_in', str(SocketType.PULL_CONNECT),
            '--socket_out', str(SocketType.PUSH_CONNECT),
            '--yaml_path', 'BaseRouter',
        ])

        with RouterService(p_args), FrontendService(args):
            CLIClient(self.train_args)
            CLIClient(self.index_args)
            CLIClient(self.query_args)

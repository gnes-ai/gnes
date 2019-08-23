import os
import unittest

import grpc

from gnes.cli.parser import set_frontend_parser, _set_loadable_service_parser, set_preprocessor_parser
from gnes.proto import gnes_pb2_grpc, RequestGenerator
from gnes.service.base import ServiceManager, SocketType
from gnes.service.encoder import EncoderService
from gnes.service.frontend import FrontendService
from gnes.service.preprocessor import PreprocessorService


@unittest.SkipTest
class TestEncoder(unittest.TestCase):

    def setUp(self):
        self.dirname = os.path.dirname(__file__)
        self.transformer_yml = os.path.join(self.dirname, 'contrib', 'transformer.yml')
        self.transformer_py = os.path.join(self.dirname, 'contrib', 'transformer.py')
        os.environ['GNES_CONTRIB_MODULE'] = self.transformer_py
        os.unsetenv('http_proxy')
        os.unsetenv('https_proxy')

    def test_pymode(self):
        args = set_frontend_parser().parse_args([])

        p_args = set_preprocessor_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', '5531',
            '--socket_in', str(SocketType.PULL_CONNECT),
            '--socket_out', str(SocketType.PUSH_BIND),
            '--yaml_path', '!UnaryPreprocessor {parameters: {doc_type: 1}}'
        ])

        e_args = _set_loadable_service_parser().parse_args([
            '--port_in', str(p_args.port_out),
            '--port_out', str(args.port_in),
            '--socket_in', str(SocketType.PULL_CONNECT),
            '--socket_out', str(SocketType.PUSH_CONNECT),
            '--yaml_path', self.transformer_yml,
        ])

        with ServiceManager(EncoderService, e_args), \
             ServiceManager(PreprocessorService, p_args), \
             ServiceManager(FrontendService, args), \
             grpc.insecure_channel('%s:%d' % (args.grpc_host, args.grpc_port),
                                   options=[('grpc.max_send_message_length', 70 * 1024 * 1024),
                                            ('grpc.max_receive_message_length', 70 * 1024 * 1024)]) as channel:
            stub = gnes_pb2_grpc.GnesRPCStub(channel)
            resp = stub.Call(list(RequestGenerator.index([b'hello world', b'goodbye!'], 1))[0])
            self.assertEqual(resp.request_id, 0)

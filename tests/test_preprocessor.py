import os
import unittest

from gnes.cli.parser import set_preprocessor_parser, _set_client_parser
from gnes.client.base import ZmqClient
from gnes.proto import gnes_pb2
from gnes.service.preprocessor import PreprocessorService


class TestProto(unittest.TestCase):

    def setUp(self):
        self.single_cn = '矫矫珍木巅，得无金丸惧。'
        self.single_en = 'When forty winters shall besiege thy brow. And dig deep trenches in thy beautys field.'
        self.dirname = os.path.dirname(__file__)
        self.yaml_path = os.path.join(self.dirname, 'yaml', 'test-preprocessor.yml')

    def test_preprocessor_service_empty(self):
        args = set_preprocessor_parser().parse_args(['--yaml_path', 'BasePreprocessor'])
        with PreprocessorService(args):
            pass

    def test_preprocessor_service_echo(self):
        args = set_preprocessor_parser().parse_args(['--yaml_path', 'BasePreprocessor'])
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in)
        ])
        with PreprocessorService(args), ZmqClient(c_args) as client:
            msg = gnes_pb2.Message()
            msg.request.index.docs.extend([gnes_pb2.Document() for _ in range(5)])
            client.send_message(msg)
            r = client.recv_message()
            print(r)
            msg.request.train.docs.extend([gnes_pb2.Document() for _ in range(5)])
            client.send_message(msg)
            r = client.recv_message()
            print(r)

    def test_preprocessor_service_realdata(self):
        args = set_preprocessor_parser().parse_args(['--yaml_path', self.yaml_path])
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in)
        ])
        with open(os.path.join(self.dirname, '26-doc-chinese.txt'), 'r', encoding='utf8') as fp:
            msg = gnes_pb2.Message()
            all_text = ''
            for v in fp:
                if v.strip():
                    d = msg.request.train.docs.add()
                    d.raw_bytes = v.encode()
                    all_text += v
            with PreprocessorService(args), ZmqClient(c_args) as client:
                client.send_message(msg)
                r = client.recv_message()
                print(r)

                msg1 = gnes_pb2.Message()
                msg1.request.index.docs.extend(msg.request.train.docs)

                client.send_message(msg1)
                r = client.recv_message()
                print(r)

                msg2 = gnes_pb2.Message()
                msg2.request.search.query.raw_text = all_text

                client.send_message(msg2)
                r = client.recv_message()
                print(r)

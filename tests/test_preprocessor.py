import os
import unittest

from gnes.cli.parser import set_preprocessor_service_parser, _set_client_parser
from gnes.preprocessor.text import line2pb_doc, txt_file2pb_docs
from gnes.proto import gnes_pb2
from gnes.service.grpc import ZmqClient
from gnes.service.preprocessor import PreprocessorService


class TestProto(unittest.TestCase):

    def setUp(self):
        self.single_cn = '矫矫珍木巅，得无金丸惧。'
        self.single_en = 'When forty winters shall besiege thy brow. And dig deep trenches in thy beautys field.'
        self.dirname = os.path.dirname(__file__)

    def test_single_doc(self):
        print(line2pb_doc(self.single_cn))
        print(line2pb_doc(self.single_en))

    def test_cn_file_doc(self):
        with open(os.path.join(self.dirname, '26-doc-chinese.txt'), 'r', encoding='utf8') as fp:
            self.assertEqual(len(txt_file2pb_docs(fp, 0)), 26)

    def test_en_file_doc(self):
        with open(os.path.join(self.dirname, '6-doc-english.txt'), 'r', encoding='utf8') as fp:
            self.assertEqual(len(txt_file2pb_docs(fp, 0)), 6)

    def test_request(self):
        with open(os.path.join(self.dirname, '26-doc-chinese.txt'), 'r', encoding='utf8') as fp:
            docs = txt_file2pb_docs(fp, 0)
        r = gnes_pb2.Request()
        r.train.docs.extend(docs)
        self.assertEqual(len(r.train.docs), 26)

    def test_preprocessor_service_empty(self):
        args = set_preprocessor_service_parser().parse_args([])
        with PreprocessorService(args):
            pass

    def test_preprocessor_service_echo(self):
        args = set_preprocessor_service_parser().parse_args([])
        c_args = _set_client_parser().parse_args([
            '--port_in', args.port_out,
            '--port_out', args.port_in
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
        args = set_preprocessor_service_parser().parse_args([])
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
                    d.raw_text = v
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

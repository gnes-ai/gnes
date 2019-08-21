import os
import unittest

from gnes.cli.parser import set_preprocessor_parser, _set_client_parser
from gnes.client.base import ZmqClient
from gnes.proto import gnes_pb2, RequestGenerator, blob2array
from gnes.service.preprocessor import PreprocessorService


class TestShotDetector(unittest.TestCase):

    def setUp(self):
        self.dirname = os.path.dirname(__file__)
        self.histogram_yml_path = os.path.join(self.dirname, 'yaml', 'preprocessor-shotdetect_histogram.yml')
        self.edge_yml_path = os.path.join(self.dirname, 'yaml', 'preprocessor-shotdetect_edge.yml')
        self.video_path = os.path.join(self.dirname, 'videos')

    def test_video_preprocessor_service_empty(self):
        args = set_preprocessor_parser().parse_args([
            '--yaml_path', self.histogram_yml_path
        ])
        with PreprocessorService(args):
            pass

    def test_video_preprocessor_service_realdata_histogram(self):
        args = set_preprocessor_parser().parse_args([
            '--yaml_path', self.histogram_yml_path
        ])
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in)
        ])
        video_bytes = [open(os.path.join(self.video_path, _), 'rb').read()
                       for _ in os.listdir(self.video_path)]

        with PreprocessorService(args), ZmqClient(c_args) as client:
            for req in RequestGenerator.index(video_bytes):
                msg = gnes_pb2.Message()
                msg.request.index.CopyFrom(req.index)
                client.send_message(msg)
                r = client.recv_message()
                for d in r.request.index.docs:
                    self.assertGreater(len(d.chunks), 0)
                    for _ in range(len(d.chunks)):
                        shape = blob2array(d.chunks[_].blob).shape
                        self.assertEqual(shape[1:], (168, 192, 3))

    def test_video_preprocessor_service_realdata_edge(self):
        args = set_preprocessor_parser().parse_args([
            '--yaml_path', self.edge_yml_path
        ])
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in)
        ])
        video_bytes = [open(os.path.join(self.video_path, _), 'rb').read()
                       for _ in os.listdir(self.video_path)]

        with PreprocessorService(args), ZmqClient(c_args) as client:
            for req in RequestGenerator.index(video_bytes):
                msg = gnes_pb2.Message()
                msg.request.index.CopyFrom(req.index)
                client.send_message(msg)
                r = client.recv_message()
                for d in r.request.index.docs:
                    self.assertGreater(len(d.chunks), 0)
                    for _ in range(len(d.chunks)):
                        shape = blob2array(d.chunks[_].blob).shape
                        self.assertEqual(shape[1:], (168, 192, 3))

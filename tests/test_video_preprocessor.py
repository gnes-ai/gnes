import os
import unittest

from gnes.cli.parser import set_preprocessor_service_parser, _set_client_parser
from gnes.proto import gnes_pb2, RequestGenerator, blob2array
from gnes.service.grpc import ZmqClient
from gnes.service.preprocessor import PreprocessorService


class TestFFmpeg(unittest.TestCase):

    def setUp(self):
        self.dirname = os.path.dirname(__file__)
        self.yml_path = os.path.join(self.dirname, 'yaml', 'preprocessor-ffmpeg.yml')
        self.video_path = os.path.join(self.dirname, 'videos')

    def test_video_preprocessor_service_empty(self):
        args = set_preprocessor_service_parser().parse_args([
            '--yaml_path', self.yml_path
        ])
        with PreprocessorService(args):
            pass

    def test_video_preprocessor_service_realdata(self):
        args = set_preprocessor_service_parser().parse_args([
            '--yaml_path', self.yml_path
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
                        self.assertEqual(shape, (168, 192, 3))

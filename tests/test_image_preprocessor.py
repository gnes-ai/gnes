import os
import unittest
import zipfile

from gnes.cli.parser import set_preprocessor_service_parser, _set_client_parser
from gnes.proto import gnes_pb2, RequestGenerator, blob2array
from gnes.service.grpc import ZmqClient
from gnes.service.preprocessor import PreprocessorService


class TestProto(unittest.TestCase):

    def setUp(self):
        self.dirname = os.path.dirname(__file__)
        self.singleton_img_pre_yaml = os.path.join(self.dirname, 'yaml', 'base-singleton-image-prep.yml')
        self.slidingwindow_img_pre_yaml = os.path.join(self.dirname, 'yaml', 'base-vanilla_sldwin-image-prep.yml')
        self.segmentation_img_pre_yaml = os.path.join(self.dirname, 'yaml', 'base-segmentation-image-prep.yml')

    def test_singleton_preprocessor_service_empty(self):
        args = set_preprocessor_service_parser().parse_args([
            '--yaml_path', self.singleton_img_pre_yaml
        ])
        with PreprocessorService(args):
            pass

    def test_slidingwindow_preprocessor_service_empty(self):
        args = set_preprocessor_service_parser().parse_args([
            '--yaml_path', self.slidingwindow_img_pre_yaml
        ])
        with PreprocessorService(args):
            pass

    def test_segmentation_preprocessor_service_empty(self):
        args = set_preprocessor_service_parser().parse_args([
            '--yaml_path', self.segmentation_img_pre_yaml
        ])
        with PreprocessorService(args):
            pass

    def test_singleton_preprocessor_service_echo(self):
        args = set_preprocessor_service_parser().parse_args([
            '--yaml_path', self.singleton_img_pre_yaml
        ])
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in)
        ])
        with PreprocessorService(args), ZmqClient(c_args) as client:
            msg = gnes_pb2.Message()
            msg.request.index.docs.extend([gnes_pb2.Document() for _ in range(5)])
            client.send_message(msg)
            r = client.recv_message()
            # print(r)
            msg.request.train.docs.extend([gnes_pb2.Document() for _ in range(5)])
            client.send_message(msg)
            r = client.recv_message()
            # print(r)

    def test_slidingwindow_preprocessor_service_echo(self):
        args = set_preprocessor_service_parser().parse_args([
            '--yaml_path', self.slidingwindow_img_pre_yaml
        ])
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in)
        ])
        with PreprocessorService(args), ZmqClient(c_args) as client:
            msg = gnes_pb2.Message()
            msg.request.index.docs.extend([gnes_pb2.Document() for _ in range(5)])
            client.send_message(msg)
            r = client.recv_message()
            # print(r)
            msg.request.train.docs.extend([gnes_pb2.Document() for _ in range(5)])
            client.send_message(msg)
            r = client.recv_message()
            # print(r)

    def test_segmentation_preprocessor_service_echo(self):
        args = set_preprocessor_service_parser().parse_args([
            '--yaml_path', self.segmentation_img_pre_yaml
        ])
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in)
        ])
        with PreprocessorService(args), ZmqClient(c_args) as client:
            msg = gnes_pb2.Message()
            msg.request.index.docs.extend([gnes_pb2.Document() for _ in range(5)])
            client.send_message(msg)
            r = client.recv_message()
            # print(r)
            msg.request.train.docs.extend([gnes_pb2.Document() for _ in range(5)])
            client.send_message(msg)
            r = client.recv_message()
            # print(r)

    def test_singleton_preprocessor_service_realdata(self):
        args = set_preprocessor_service_parser().parse_args([
            '--yaml_path', self.singleton_img_pre_yaml
        ])
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in)
        ])
        all_zips = zipfile.ZipFile(os.path.join(self.dirname, 'imgs/test.zip'))
        all_bytes = [all_zips.open(v).read() for v in all_zips.namelist()]

        with PreprocessorService(args), ZmqClient(c_args) as client:
            for req in RequestGenerator.index(all_bytes):
                msg = gnes_pb2.Message()
                msg.request.index.CopyFrom(req.index)
                client.send_message(msg)
                r = client.recv_message()
                self.assertEqual(r.envelope.routes[0].service, 'PreprocessorService:BaseSingletonPreprocessor')
                for d in r.request.index.docs:
                    self.assertEqual(len(d.chunks), 1)
                    self.assertEqual(len(blob2array(d.chunks[0].blob).shape), 3)
                    self.assertEqual(blob2array(d.chunks[0].blob).shape[-1], 3)
                    self.assertEqual(blob2array(d.chunks[0].blob).shape[0], 224)
                    self.assertEqual(blob2array(d.chunks[0].blob).shape[1], 224)
                    print(blob2array(d.chunks[0].blob).dtype)

    def test_slidingwindow_preprocessor_service_realdata(self):
        args = set_preprocessor_service_parser().parse_args([
            '--yaml_path', self.slidingwindow_img_pre_yaml
        ])

        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in)
        ])
        all_zips = zipfile.ZipFile(os.path.join(self.dirname, 'imgs/test.zip'))
        all_bytes = [all_zips.open(v).read() for v in all_zips.namelist()]

        with PreprocessorService(args), ZmqClient(c_args) as client:
            for req in RequestGenerator.index(all_bytes):
                msg = gnes_pb2.Message()
                msg.request.index.CopyFrom(req.index)
                client.send_message(msg)
                r = client.recv_message()
                self.assertEqual(r.envelope.routes[0].service, 'PreprocessorService:VanillaSlidingPreprocessor')
                for d in r.request.index.docs:
                    self.assertEqual(len(blob2array(d.chunks[0].blob).shape), 3)
                    self.assertEqual(blob2array(d.chunks[0].blob).shape[-1], 3)
                    self.assertEqual(blob2array(d.chunks[0].blob).shape[0], 224)
                    self.assertEqual(blob2array(d.chunks[0].blob).shape[1], 224)
                    print(blob2array(d.chunks[0].blob).dtype)

    def test_segmentation_preprocessor_service_realdata(self):
        args = set_preprocessor_service_parser().parse_args([
            '--yaml_path', self.segmentation_img_pre_yaml
        ])

        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in)
        ])
        all_zips = zipfile.ZipFile(os.path.join(self.dirname, 'imgs/test.zip'))
        all_bytes = [all_zips.open(v).read() for v in all_zips.namelist()]

        with PreprocessorService(args), ZmqClient(c_args) as client:
            for req in RequestGenerator.index(all_bytes):
                msg = gnes_pb2.Message()
                msg.request.index.CopyFrom(req.index)
                client.send_message(msg)
                r = client.recv_message()
                self.assertEqual(r.envelope.routes[0].service, 'PreprocessorService:SegmentPreprocessor')
                for d in r.request.index.docs:
                    self.assertEqual(len(blob2array(d.chunks[0].blob).shape), 3)
                    self.assertEqual(blob2array(d.chunks[0].blob).shape[-1], 3)
                    self.assertEqual(blob2array(d.chunks[0].blob).shape[0], 224)
                    self.assertEqual(blob2array(d.chunks[0].blob).shape[1], 224)
                    print(blob2array(d.chunks[0].blob).dtype)
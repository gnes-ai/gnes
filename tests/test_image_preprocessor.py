import os
import unittest

from gnes.cli.parser import set_preprocessor_service_parser, _set_client_parser
from gnes.proto import gnes_pb2
from gnes.service.grpc import ZmqClient
from gnes.service.preprocessor import PreprocessorService
import zipfile
from PIL import Image
import numpy as np


class TestProto(unittest.TestCase):

    def setUp(self):
        self.dirname = os.path.dirname(__file__)

    def test_preprocessor_service_empty(self):
        args = set_preprocessor_service_parser().parse_args([])
        with PreprocessorService(args):
            pass

    def test_preprocessor_service_echo(self):
        args = set_preprocessor_service_parser().parse_args([])
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

    def test_preprocessor_service_realdata(self):
        args = set_preprocessor_service_parser().parse_args([])
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in)
        ])
        zipfile_ = zipfile.ZipFile(os.path.join(self.dirname, 'imgs/test.zip'), "r")
        imgs_list = zipfile_.namelist()
        msg = gnes_pb2.Message()
        for img_file in imgs_list:
            image = Image.open(zipfile_.open(img_file, 'r'))
            image_asarray = np.asarray(image, dtype=np.float32)
            d = msg.request.train.docs.add()
            d.raw_image.data = image.tobytes()
            d.raw_image.shape.extend(image.size)
            d.raw_image.dtype = image_asarray.dtype.name
        with PreprocessorService(args), ZmqClient(c_args) as client:
            client.send_message(msg)
            r = client.recv_message()
            # print(r)

            msg1 = gnes_pb2.Message()
            msg1.request.index.docs.extend(msg.request.train.docs)

            client.send_message(msg1)
            r = client.recv_message()
            # print(r)

            msg2 = gnes_pb2.Message()
            image = Image.open(zipfile_.open(imgs_list[0], 'r'))
            image_asarray = np.asarray(image, dtype=np.float32)

            msg2.request.search.query.raw_image.data = image.tobytes()
            msg2.request.search.query.raw_image.shape.extend(image.size)
            msg2.request.search.query.raw_image.dtype = image_asarray.dtype.name

            client.send_message(msg2)
            r = client.recv_message()
            print(r)


import os
import unittest

import numpy as np

from gnes.cli.parser import set_encoder_parser, _set_client_parser
from gnes.client.base import ZmqClient
from gnes.proto import gnes_pb2, array2blob
from gnes.service.base import ServiceManager
from gnes.service.encoder import EncoderService


class TestEncoderService(unittest.TestCase):

    def setUp(self):
        self.test_numeric = np.random.randint(0, 255, (1000, 1024)).astype('float32')

    def test_empty_service(self):
        args = set_encoder_parser().parse_args(['--yaml_path', '!BaseImageEncoder {gnes_config: {name: EncoderService}}'])
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in)])

        with ServiceManager(EncoderService, args), ZmqClient(c_args) as client:
            msg = gnes_pb2.Message()
            d = msg.request.index.docs.add()
            d.doc_id = 0
            d.raw_bytes = self.test_numeric.tobytes()
            d.doc_type = gnes_pb2.Document.TEXT
            msg.envelope.num_part.append(1)

            c = d.chunks.add()
            c.doc_id = d.doc_id
            c.blob.CopyFrom(array2blob(self.test_numeric))
            c.offset = 0
            c.weight = 1.0

            client.send_message(msg)
            r = client.recv_message()
            self.assertEqual(len(r.request.index.docs), 1)

    def tearDown(self):
        if os.path.exists('EncoderService.bin'):
            os.remove('EncoderService.bin')

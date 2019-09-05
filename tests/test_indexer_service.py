import os
import unittest

import numpy as np

from gnes.cli.parser import set_indexer_parser, _set_client_parser
from gnes.client.base import ZmqClient
from gnes.proto import gnes_pb2, array2blob
from gnes.service.base import ServiceManager
from gnes.service.indexer import IndexerService


class TestIndexerService(unittest.TestCase):

    def setUp(self):
        self.test_numeric = np.random.randint(0, 255, (1000, 1024)).astype('float32')

    def test_empty_service(self):
        args = set_indexer_parser().parse_args(['--yaml_path', '!BaseChunkIndexer {gnes_config: {name: IndexerService}}'])
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in)])

        with ServiceManager(IndexerService, args), ZmqClient(c_args) as client:
            msg = gnes_pb2.Message()
            d = msg.request.index.docs.add()

            c = d.chunks.add()
            c.doc_id = 0
            c.embedding.CopyFrom(array2blob(self.test_numeric))
            c.offset = 0
            c.weight = 1.0

            client.send_message(msg)
            r = client.recv_message()
            self.assertEqual(r.response.index.status, gnes_pb2.Response.SUCCESS)

    def tearDown(self):
        if os.path.exists('IndexerService.bin'):
            os.remove('IndexerService.bin')

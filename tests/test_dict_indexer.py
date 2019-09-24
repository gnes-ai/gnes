import os
import unittest
from shutil import rmtree

import grpc

from gnes.cli.parser import set_frontend_parser, set_preprocessor_parser, set_indexer_parser
from gnes.indexer.base import BaseIndexer
from gnes.indexer.doc.filesys import DirectoryIndexer
from gnes.preprocessor.base import BasePreprocessor
from gnes.proto import gnes_pb2, gnes_pb2_grpc, RequestGenerator
from gnes.service.base import SocketType, ServiceManager
from gnes.service.frontend import FrontendService
from gnes.service.indexer import IndexerService
from gnes.service.preprocessor import PreprocessorService


class TestDictIndexer(unittest.TestCase):
    def setUp(self):
        self.dirname = os.path.dirname(__file__)

        self.video_path = os.path.join(self.dirname, 'videos')
        self.video_bytes = [open(os.path.join(self.video_path, _), 'rb').read()
                            for _ in os.listdir(self.video_path)]

        self.pipeline_name = 'pipe-gif'
        self.pipeline_yml_path = os.path.join(self.dirname, 'yaml/%s.yml' % self.pipeline_name)
        self.data_path = './test_chunkleveldb'
        self.dump_path = os.path.join(self.dirname, 'indexer.bin')

        self.init_db()

    def test_pymode(self):
        os.unsetenv('http_proxy')
        os.unsetenv('https_proxy')
        args = set_frontend_parser().parse_args([
            '--dump_route', 'test.json'
        ])

        p_args = set_preprocessor_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', '5531',
            '--socket_in', str(SocketType.PULL_CONNECT),
            '--socket_out', str(SocketType.PUSH_BIND),
            '--yaml_path', 'SentSplitPreprocessor'
        ])

        e_args = set_indexer_parser().parse_args([
            '--port_in', str(p_args.port_out),
            '--port_out', str(args.port_in),
            '--socket_in', str(SocketType.PULL_CONNECT),
            '--socket_out', str(SocketType.PUSH_CONNECT),
            '--yaml_path', '!DictIndexer {gnes_config: {name: dummy_dict_indexer}}',
        ])

        with ServiceManager(IndexerService, e_args), \
             ServiceManager(PreprocessorService, p_args), \
             FrontendService(args), \
             grpc.insecure_channel('%s:%s' % (args.grpc_host, args.grpc_port),
                                   options=[('grpc.max_send_message_length', 70 * 1024 * 1024),
                                            ('grpc.max_receive_message_length', 70 * 1024 * 1024)]) as channel:
            stub = gnes_pb2_grpc.GnesRPCStub(channel)
            all_bytes = []
            with open(os.path.join(self.dirname, '26-doc-chinese.txt'), 'r', encoding='utf8') as fp:
                for v in fp:
                    if v.strip():
                        all_bytes.append(v.encode())
            for r in stub.StreamCall(RequestGenerator.index(all_bytes)):
                print(r)

        bi = BaseIndexer.load('dummy_dict_indexer.bin')
        self.assertEqual(bi.num_docs, 26)
        print(bi.query([0]))

    def tearDown(self):
        if os.path.exists(self.data_path):
            rmtree(self.data_path)
        if os.path.exists('dummy_dict_indexer.bin'):
            os.remove('dummy_dict_indexer.bin')

    def init_db(self):
        self.db = DirectoryIndexer(self.data_path)

        self.d = gnes_pb2.Document()
        self.d.doc_id = 0
        self.d.raw_bytes = self.video_bytes[0]

        preprocess = BasePreprocessor.load_yaml(self.pipeline_yml_path)
        preprocess.apply(self.d)

        self.db.add(list(range(len(self.video_bytes))), [self.d])
        self.assertEqual(self.db.num_docs, len(self.video_bytes))

    def test_add_docs(self):
        # self.init_db()
        self.assertTrue(os.path.exists(os.path.join(self.data_path, str(self.d.doc_id))))
        self.assertEqual(len(self.d.chunks), len(os.listdir(os.path.join(self.data_path, str(self.d.doc_id)))) - 1)

    def test_query_docs(self):
        # self.init_db()

        query_list = [0, 1, 2]
        res = self.db.query(query_list)
        num_non_empty = sum(1 for d in res if d)
        self.assertEqual(num_non_empty, 1)

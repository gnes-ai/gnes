import os
import unittest

from gnes.cli.parser import set_encoder_service_parser, set_proxy_service_parser, set_client_parser, set_indexer_service_parser
from gnes.service.base import BaseService
from gnes.service.client import ClientService
from gnes.service.encoder import EncoderService
from gnes.service.indexer import IndexerService

from gnes.service.proxy import MapProxyService, ReduceProxyService, ProxyService


class TestEncoderService(unittest.TestCase):
    dirname = os.path.dirname(__file__)
    dump_path = os.path.join(dirname, 'encoder.bin')
    data_path = os.path.join(dirname, 'tangshi.txt')
    encoder_yaml_path = os.path.join(dirname, 'yaml', 'base-encoder.yml')

    def setUp(self):
        self.test_querys = []
        self.test_docs = []
        with open(self.data_path) as f:
            title = ''
            sents = []
            for line in f:
                line = line.strip()

                if line and not title:
                    title = line
                    sents.append(line)
                elif line and title:
                    sents.append(line)
                elif not line and title and len(sents) > 1:
                    self.test_docs.append(sents)

                    sents.clear()
                    title = ''



    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.dump_path):
            os.remove(cls.dump_path)

    def test_encoder_service_train(self):
        # test training
        m_args = set_proxy_service_parser().parse_args([
            '--port_in', '1111',
            '--port_out', '1112',
            '--socket_in', 'PULL_BIND',
            '--socket_out', 'PUSH_BIND',
        ])

        e_args = set_encoder_service_parser().parse_args([
            '--port_in', str(m_args.port_out),
            '--port_out', '1113',
            '--socket_in', 'PULL_CONNECT',
            '--socket_out', 'PUSH_BIND',
            '--mode', 'TRAIN',
            '--dump_path', self.dump_path,
            '--yaml_path', self.encoder_yaml_path
            ])

        i_args = set_indexer_service_parser().parse_args([
            '--port_in', str(e_args.port_out),
            '--port_out', '1114',
            '--socket_in', 'PULL_CONNECT',
            '--socket_out', 'PUSH_BIND',
            '--mode', 'INDEX'
            ])

        c_args = set_client_parser().parse_args([
            '--port_in', str(i_args.port_out),
            '--port_out', str(m_args.port_in),
            '--socket_out', 'PUSH_CONNECT',
            '--socket_in', 'PULL_CONNECT',
            '--wait_reply'
        ])

        with ProxyService(m_args), \
             EncoderService(e_args), \
             IndexerService(i_args), \
             ClientService(c_args) as cs:
            cs.index(self.test_docs, is_train=True)
            print('train is done! ..............')
            result = cs.index(self.test_docs)
            print('index is done! ...............')
            result = cs.query(self.test_docs[0], top_k=2)
            print(result)



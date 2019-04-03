import os
import unittest

import zmq

from gnes.cli.parser import set_service_parser, set_encoder_service_parser
from gnes.service import BaseService, EncoderService, Message, send_message


class TestService(unittest.TestCase):
    dirname = os.path.dirname(__file__)
    dump_path = os.path.join(dirname, 'encoder.bin')
    data_path = os.path.join(dirname, 'tangshi.txt')
    encoder_yaml_path = os.path.join(dirname, 'yaml', 'base-encoder.yml')

    def setUp(self):
        if 'BERT_CI_PORT' not in os.environ:
            os.environ['BERT_CI_PORT'] = '7125'
        if 'BERT_CI_PORT_OUT' not in os.environ:
            os.environ['BERT_CI_PORT_OUT'] = '7126'
        if 'BERT_CI_MODEL' not in os.environ:
            os.environ['BERT_CI_MODEL'] = '/ext_data/chinese_L-12_H-768_A-12/'
        with open(self.data_path, encoding='utf8') as fp:
            self.test_data1 = [v for v in fp if v.strip()]

    def tearDownClass(cls):
        if os.path.exists(cls.dump_path):
            os.remove(cls.dump_path)

    def test_service_open_close(self):
        args = set_service_parser().parse_args([])
        with BaseService(args) as bs:
            self.assertTrue(bs.is_ready)

    def test_encoder_service_train(self):
        # test training
        parser = set_encoder_service_parser()
        args = parser.parse_args(['--mode', 'TRAIN',
                                  '--dump_path', self.dump_path,
                                  '--yaml_path', self.encoder_yaml_path])
        with zmq.Context() as ctx, EncoderService(args):
            ctx.setsockopt(zmq.LINGER, 0)
            with ctx.socket(zmq.PUSH) as in_sock:
                in_sock.connect('tcp://%s:%d' % (args.host, args.port_in))
                send_message(in_sock, Message(msg_content=self.test_data1))
                while not os.path.exists(self.dump_path):
                    pass

    # def test_index_service(self):
    #     # test encode
    #     parser = set_encoder_service_parser()
    #     args = parser.parse_args(['--mode', 'ADD',
    #                               '--dump_path', self.dump_path])
    #     parser = set_indexer_service_parser()
    #     i_args = parser.parse_args(['--mode', 'ADD'])
    #     with zmq.Context() as ctx, EncoderService(args), IndexerService(i_args):
    #         ctx.setsockopt(zmq.LINGER, 0)
    #         with ctx.socket(zmq.PUSH) as in_sock:
    #             in_sock.connect('tcp://%s:%d' % (args.host, args.port_in))
    #             try:
    #                 send_message(in_sock, Message(msg_content=self.test_data1))
    #             except TimeoutError:
    #                 print('indexer is not started, output is timeout')
    #             countdown(20)

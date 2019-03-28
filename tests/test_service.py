import os
import unittest

import zmq

from gnes.cli.parser import set_encoder_service_parser, set_service_parser
from gnes.service import EncoderService, send_message, Message, BaseService


class TestService(unittest.TestCase):
    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'encoder.bin')
        self.data_path = os.path.join(dirname, 'tangshi.txt')
        with open(self.data_path, encoding='utf8') as fp:
            self.test_data1 = [v for v in fp if v.strip()]

    def tearDown(self):
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)

    def test_service_open_close(self):
        args = set_service_parser().parse_args([])
        with BaseService(args) as bs:
            self.assertTrue(bs.is_ready)

    def test_encoder_service_train(self):
        # test training
        parser = set_encoder_service_parser()
        args = parser.parse_args(['--train', '--model_path', self.dump_path])
        with zmq.Context() as ctx, EncoderService(args):
            ctx.setsockopt(zmq.LINGER, 0)
            with ctx.socket(zmq.PUSH) as in_sock:
                in_sock.connect('tcp://%s:%d' % (args.host, args.port_in))
                send_message(in_sock, Message(msg_content=self.test_data1))
                while not os.path.exists(self.dump_path):
                    pass

        # test encode
        # args = parser.parse_args(['--model_path', self.dump_path])
        # with zmq.Context() as ctx, EncoderService(args):
        #     ctx.setsockopt(zmq.LINGER, 0)
        #     with ctx.socket(zmq.PUSH) as in_sock:
        #         in_sock.connect('tcp://%s:%d' % (args.host, args.port_in))
        #         try:
        #             send_message(in_sock, Message(msg_content=self.test_data1))
        #         except TimeoutError:
        #             print('indexer is not started, output is timeout')
        #         countdown(20)

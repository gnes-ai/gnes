import os
import unittest

from gnes.cli.parser import set_service_parser, set_proxy_service_parser
from gnes.proto import gnes_pb2
from gnes.service.base import BaseService
from gnes.service.proxy import ProxyService


class TestService(unittest.TestCase):
    dirname = os.path.dirname(__file__)
    dump_path = os.path.join(dirname, 'encoder.bin')
    data_path = os.path.join(dirname, 'tangshi.txt')
    encoder_yaml_path = os.path.join(dirname, 'yaml', 'base-encoder.yml')

    def setUp(self):
        self.test_querys = []
        self.test_docs = []
        with open(self.data_path, encoding='utf8') as f:
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

    def test_service_open_close(self):
        args = set_service_parser().parse_args([])
        with BaseService(args) as bs:
            self.assertTrue(bs.is_ready)

    def test_service_no_event_loop(self):
        p_args = set_proxy_service_parser().parse_args([
            '--port_in',
            '5310',
            '--port_out',
            '5311',
            '--socket_in',
            'PULL_BIND',
            '--socket_out',
            'PUSH_BIND',
        ])
        args = set_service_parser().parse_args([
            '--port_out',
            '5310',
            '--port_in',
            '5311',
            '--socket_in',
            'PULL_CONNECT',
            '--socket_out',
            'PUSH_CONNECT',
        ])
        with ProxyService(p_args), BaseService(
                args, use_event_loop=False) as bs:
            msg = gnes_pb2.Message()
            bs.send_message(msg)
            msg2 = bs.recv_message()

        self.assertNotEqual(msg, msg2)

    def test_map_proxy_pub_sub_service(self):
        m_args = set_proxy_service_parser().parse_args([
            '--port_in',
            '1111',
            '--port_out',
            '1112',
            '--socket_in',
            'PULL_BIND',
            '--socket_out',
            'PUSH_BIND',
        ])

        # dummy work for simple forwarding
        w_args = set_proxy_service_parser().parse_args([
            '--port_in',
            str(m_args.port_out),
            '--port_out',
            '1113',
            '--socket_in',
            'PULL_CONNECT',
            '--socket_out',
            'PUSH_CONNECT',
        ])

        r_args = set_proxy_service_parser().parse_args([
            '--port_in',
            str(w_args.port_out),
            '--port_out',
            '1114',
            '--socket_in',
            'PULL_BIND',
            '--socket_out',
            'PUSH_BIND',
        ])

        args = set_service_parser().parse_args([
            '--port_in',
            str(r_args.port_out),    # receive from reducer-proxy
            '--port_out',
            str(m_args.port_in),    # send to mapper-proxy
            '--socket_in',
            'PULL_CONNECT',
            '--socket_out',
            'PUSH_CONNECT',
        ])

        with ProxyService(m_args), \
             ProxyService(w_args), \
             ProxyService(r_args), \
             BaseService(args, use_event_loop=False) as bs:
            msg = gnes_pb2.Message()
            bs.send_message(msg)
            msg2 = bs.recv_message()
        self.assertNotEqual(msg, msg2)

        # with muliple dummy workers
        with ProxyService(m_args), \
             ProxyService(w_args), \
             ProxyService(w_args), \
             ProxyService(w_args), \
             ProxyService(w_args), \
             ProxyService(r_args), \
             BaseService(args, use_event_loop=False) as bs:

            msg = gnes_pb2.Message()
            bs.send_message(msg)
            msg2 = bs.recv_message()
        self.assertNotEqual(msg, msg2)

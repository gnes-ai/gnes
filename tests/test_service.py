import os
import unittest

from gnes.cli.parser import set_service_parser, set_proxy_service_parser, set_client_parser
from gnes.service import BaseService, ProxyService, ClientService
from gnes.service.proxy import MapProxyService, ReduceProxyService


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

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.dump_path):
            os.remove(cls.dump_path)

    def test_service_open_close(self):
        args = set_service_parser().parse_args([])
        with BaseService(args) as bs:
            self.assertTrue(bs.is_ready)

    def test_proxy_service(self):
        p_args = set_proxy_service_parser().parse_args([
            '--socket_in', 'PULL_BIND',
            '--socket_out', 'PUSH_BIND',
        ])
        c_args = set_client_parser().parse_args([
            '--port_in', str(p_args.port_out),
            '--port_out', str(p_args.port_in),
            '--socket_in', 'PULL_CONNECT',
            '--socket_out', 'PUSH_CONNECT',
            '--wait_reply'
        ])
        with ProxyService(p_args), ClientService(c_args) as cs:
            result = cs.query(self.test_data1)
            self.assertEqual(result.msg_content, self.test_data1)

    def test_map_proxy_pub_sub_service(self):
        m_args = set_proxy_service_parser().parse_args([
            '--port_in', '1111',
            '--port_out', '1112',
            '--socket_in', 'PULL_BIND',
            '--socket_out', 'PUB_BIND',
        ])
        r_args = set_proxy_service_parser().parse_args([
            '--port_in', '1113',
            '--port_out', '1114',
            '--socket_in', 'PULL_BIND',
            '--socket_out', 'PUSH_BIND',
        ])
        r1_args = set_proxy_service_parser().parse_args([
            '--port_in', '1113',
            '--port_out', '1114',
            '--socket_in', 'PULL_BIND',
            '--socket_out', 'PUSH_BIND',
            '--num_part', '4'
        ])
        # dummy work for simple forwarding
        w_args = set_proxy_service_parser().parse_args([
            '--port_in', str(m_args.port_out),
            '--port_out', str(r_args.port_in),
            '--socket_in', 'SUB_CONNECT',
            '--socket_out', 'PUSH_CONNECT',
        ])
        c_args = set_client_parser().parse_args([
            '--port_in', str(r_args.port_out),  # receive from reducer-proxy
            '--port_out', str(m_args.port_in),  # send to mapper-proxy
            '--socket_in', 'PULL_CONNECT',
            '--socket_out', 'PUSH_CONNECT',
            '--wait_reply'
        ])

        with ProxyService(m_args), \
             ReduceProxyService(r_args), \
             ProxyService(w_args), \
             ClientService(c_args) as cs:
            result = cs.query(self.test_data1)
            self.assertEqual(result.msg_content, self.test_data1)

        # with muliple dummy workers
        with ProxyService(m_args), \
             ReduceProxyService(r1_args), \
             ProxyService(w_args), \
             ProxyService(w_args), \
             ProxyService(w_args), \
             ProxyService(w_args), \
             ClientService(c_args) as cs:
            result = cs.query(self.test_data1)
            self.assertEqual(result.msg_content, self.test_data1 * 4)

    def test_map_proxy_service(self):
        m_args = set_proxy_service_parser().parse_args([
            '--port_in', '1111',
            '--port_out', '1112',
            '--socket_in', 'PULL_BIND',
            '--socket_out', 'PUSH_BIND',
            '--batch_size', '10'
        ])
        r_args = set_proxy_service_parser().parse_args([
            '--port_in', '1113',
            '--port_out', '1114',
            '--socket_in', 'PULL_BIND',
            '--socket_out', 'PUSH_BIND',
        ])
        # dummy work for simple forwarding
        w_args = set_proxy_service_parser().parse_args([
            '--port_in', str(m_args.port_out),
            '--port_out', str(r_args.port_in),
            '--socket_in', 'PULL_CONNECT',
            '--socket_out', 'PUSH_CONNECT',
        ])

        c_args = set_client_parser().parse_args([
            '--port_in', str(r_args.port_out),  # receive from reducer-proxy
            '--port_out', str(m_args.port_in),  # send to mapper-proxy
            '--socket_in', 'PULL_CONNECT',
            '--socket_out', 'PUSH_CONNECT',
            '--wait_reply'
        ])
        with MapProxyService(m_args), \
             ReduceProxyService(r_args), \
             ProxyService(w_args), \
             ClientService(c_args) as cs:
            result = cs.query(self.test_data1)
            self.assertEqual(result.msg_content, self.test_data1)

        # with muliple dummy workers
        with MapProxyService(m_args), \
             ReduceProxyService(r_args), \
             ProxyService(w_args), \
             ProxyService(w_args), \
             ProxyService(w_args), \
             ProxyService(w_args), \
             ClientService(c_args) as cs:
            result = cs.query(self.test_data1)
            self.assertEqual(result.msg_content, self.test_data1)

    # def test_encoder_service_train(self):
    #     # test training
    #     parser = set_encoder_service_parser()
    #     args = parser.parse_args(['--mode', 'TRAIN',
    #                               '--dump_path', self.dump_path,
    #                               '--yaml_path', self.encoder_yaml_path])
    #     with zmq.Context() as ctx, EncoderService(args):
    #         ctx.setsockopt(zmq.LINGER, 0)
    #         with ctx.socket(zmq.PUSH) as in_sock:
    #             in_sock.connect('tcp://%s:%d' % (args.host, args.port_in))
    #             send_message(in_sock, Message(msg_content=self.test_data1))
    #             while not os.path.exists(self.dump_path):
    #                 pass

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

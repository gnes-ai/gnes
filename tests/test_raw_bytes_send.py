import random
import unittest

from gnes.cli.parser import _set_client_parser
from gnes.client.base import ZmqClient
from gnes.helper import TimeContext
from gnes.proto import gnes_pb2
from gnes.service.base import SocketType


class TestProto(unittest.TestCase):
    def setUp(self):
        self.c1_args = _set_client_parser().parse_args([
            '--port_in', str(5678),
            '--port_out', str(5679),
            '--socket_out', str(SocketType.PUSH_BIND),
            '--no-check_version'
        ])
        self.c2_args = _set_client_parser().parse_args([
            '--port_in', str(self.c1_args.port_out),
            '--port_out', str(self.c1_args.port_in),
            '--socket_in', str(SocketType.PULL_CONNECT),
            '--no-check_version'
        ])

    def test_send_recv(self):
        with ZmqClient(self.c1_args) as c1, ZmqClient(self.c2_args) as c2:
            msg = gnes_pb2.Message()
            msg.envelope.client_id = c1.args.identity
            d = msg.request.index.docs.add()
            d.raw_bytes = b'aa'
            c1.send_message(msg)
            r_msg = c2.recv_message()
            self.assertEqual(r_msg.request.index.docs[0].raw_bytes, d.raw_bytes)

    def test_send_recv_raw_bytes(self):
        with ZmqClient(self.c1_args) as c1, ZmqClient(self.c2_args) as c2:
            msg = gnes_pb2.Message()
            msg.envelope.client_id = c1.args.identity
            for j in range(random.randint(10, 20)):
                d = msg.request.index.docs.add()
                d.raw_bytes = b'a' * random.randint(100, 1000)
            c1.send_message(msg, raw_bytes_in_separate=True)
            r_msg = c2.recv_message()
            for d, r_d in zip(msg.request.index.docs, r_msg.request.index.docs):
                self.assertEqual(d.raw_bytes, r_d.raw_bytes)
                print('.', end='')
            print('checked %d docs' % len(msg.request.index.docs))

    def test_benchmark(self):
        all_msgs = []
        num_msg = 20
        for j in range(num_msg):
            msg = gnes_pb2.Message()
            msg.envelope.client_id = 'abc'
            for j in range(random.randint(10, 20)):
                d = msg.request.index.docs.add()
                # each doc is about 1MB to 10MB
                d.raw_bytes = b'a' * random.randint(1000000, 10000000)
            all_msgs.append(msg)

        with ZmqClient(self.c1_args) as c1, ZmqClient(self.c2_args) as c2:
            with TimeContext('send, raw_bytes_in_separate=False'):
                for m in all_msgs:
                    c1.send_message(m)
            with TimeContext('recv, raw_bytes_in_separate=False'):
                for _ in all_msgs:
                    c2.recv_message()

        with ZmqClient(self.c1_args) as c1, ZmqClient(self.c2_args) as c2:
            with TimeContext('send, raw_bytes_in_separate=True'):
                for m in all_msgs:
                    c1.send_message(m, raw_bytes_in_separate=True)
            with TimeContext('recv, raw_bytes_in_separate=True'):
                for _ in all_msgs:
                    c2.recv_message()

        with ZmqClient(self.c1_args) as c1, ZmqClient(self.c2_args) as c2:
            with TimeContext('send->recv, raw_bytes_in_separate=False'):
                for m in all_msgs:
                    c1.send_message(m, raw_bytes_in_separate=False)
                    c2.recv_message()

        with ZmqClient(self.c1_args) as c1, ZmqClient(self.c2_args) as c2:
            with TimeContext('send->recv, raw_bytes_in_separate=True'):
                for m in all_msgs:
                    c1.send_message(m, raw_bytes_in_separate=True)
                    c2.recv_message()

        with ZmqClient(self.c1_args) as c1, ZmqClient(self.c2_args) as c2:
            for m in all_msgs:
                c1.send_message(m, raw_bytes_in_separate=True)
                r_m = c2.recv_message()
                for d, r_d in zip(m.request.index.docs, r_m.request.index.docs):
                    self.assertEqual(d.raw_bytes, r_d.raw_bytes)

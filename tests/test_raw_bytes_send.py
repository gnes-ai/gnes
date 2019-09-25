import copy
import random
import unittest

import numpy as np

from gnes.cli.parser import _set_client_parser
from gnes.client.base import ZmqClient
from gnes.helper import TimeContext
from gnes.proto import gnes_pb2, array2blob, blob2array
from gnes.service.base import SocketType


class TestSqueezedSendRecv(unittest.TestCase):
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
            raw_bytes = copy.deepcopy([d.raw_bytes for d in msg.request.index.docs])
            c1.send_message(msg, squeeze_pb=True)
            r_msg = c2.recv_message()
            for d, o_d, r_d in zip(msg.request.index.docs, raw_bytes, r_msg.request.index.docs):
                self.assertEqual(d.raw_bytes, b'')
                self.assertEqual(o_d, r_d.raw_bytes)
                print('.', end='')
            print('checked %d docs' % len(msg.request.index.docs))

    def test_send_recv_response(self):
        with ZmqClient(self.c1_args) as c1, ZmqClient(self.c2_args) as c2:
            msg = gnes_pb2.Message()
            msg.envelope.client_id = c1.args.identity
            msg.response.train.status = 2
            c1.send_message(msg, squeeze_pb=True)
            r_msg = c2.recv_message()
            self.assertEqual(msg.response.train.status, r_msg.response.train.status)

    def build_msgs(self):
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
        return all_msgs

    def build_msgs2(self, seed=0):
        all_msgs = []
        num_msg = 20
        random.seed(seed)
        np.random.seed(seed)
        for j in range(num_msg):
            msg = gnes_pb2.Message()
            msg.envelope.client_id = 'abc'
            for _ in range(random.randint(10, 20)):
                d = msg.request.index.docs.add()
                # each doc is about 1MB to 10MB
                for _ in range(random.randint(10, 20)):
                    c = d.chunks.add()
                    c.embedding.CopyFrom(array2blob(np.random.random([10, 20, 30])))
                    c.blob.CopyFrom(array2blob(np.random.random([10, 20, 30])))
            all_msgs.append(msg)
        return all_msgs

    def test_benchmark(self):
        all_msgs = self.build_msgs()

        with ZmqClient(self.c1_args) as c1, ZmqClient(self.c2_args) as c2:
            with TimeContext('send, squeeze_pb=False'):
                for m in all_msgs:
                    c1.send_message(m)
            with TimeContext('recv, squeeze_pb=False'):
                for _ in all_msgs:
                    c2.recv_message()

        with ZmqClient(self.c1_args) as c1, ZmqClient(self.c2_args) as c2:
            with TimeContext('send, squeeze_pb=True'):
                for m in all_msgs:
                    c1.send_message(m, squeeze_pb=True)
            with TimeContext('recv, squeeze_pb=True'):
                for _ in all_msgs:
                    c2.recv_message()

    def test_benchmark2(self):
        all_msgs = self.build_msgs()

        with ZmqClient(self.c1_args) as c1, ZmqClient(self.c2_args) as c2:
            with TimeContext('send->recv, squeeze_pb=False'):
                for m in all_msgs:
                    c1.send_message(m, squeeze_pb=False)
                    c2.recv_message()

        with ZmqClient(self.c1_args) as c1, ZmqClient(self.c2_args) as c2:
            with TimeContext('send->recv, squeeze_pb=True'):
                for m in all_msgs:
                    c1.send_message(m, squeeze_pb=True)
                    c2.recv_message()

    def test_benchmark3(self):
        all_msgs = self.build_msgs()
        all_msgs_bak = copy.deepcopy(all_msgs)

        with ZmqClient(self.c1_args) as c1, ZmqClient(self.c2_args) as c2:
            for m, m1 in zip(all_msgs, all_msgs_bak):
                c1.send_message(m, squeeze_pb=True)
                r_m = c2.recv_message()
                for d, o_d, r_d in zip(m.request.index.docs, m1.request.index.docs, r_m.request.index.docs):
                    self.assertEqual(d.raw_bytes, b'')
                    self.assertEqual(o_d.raw_bytes, r_d.raw_bytes)

    def test_benchmark4(self):
        all_msgs = self.build_msgs2()

        with ZmqClient(self.c1_args) as c1, ZmqClient(self.c2_args) as c2:
            with TimeContext('send->recv, squeeze_pb=False'):
                for m in all_msgs:
                    c1.send_message(m, squeeze_pb=False)
                    c2.recv_message()

        with ZmqClient(self.c1_args) as c1, ZmqClient(self.c2_args) as c2:
            with TimeContext('send->recv, squeeze_pb=True'):
                for m in all_msgs:
                    c1.send_message(m, squeeze_pb=True)
                    c2.recv_message()

    def test_benchmark5(self):
        all_msgs = self.build_msgs2()
        all_msgs_bak = copy.deepcopy(all_msgs)

        with ZmqClient(self.c1_args) as c1, ZmqClient(self.c2_args) as c2:
            with TimeContext('send->recv, squeeze_pb=True'):
                for m, m1 in zip(all_msgs, all_msgs_bak):
                    c1.send_message(m, squeeze_pb=True)
                    r_m = c2.recv_message()

                    for d, r_d in zip(m1.request.index.docs, r_m.request.index.docs):
                        for c, r_c in zip(d.chunks, r_d.chunks):
                            np.allclose(blob2array(c.embedding), blob2array(r_c.embedding))
                            np.allclose(blob2array(c.blob), blob2array(r_c.blob))
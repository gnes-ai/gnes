import os
import unittest

from gnes.cli.parser import set_router_service_parser, _set_client_parser
from gnes.proto import gnes_pb2
from gnes.service.base import SocketType
from gnes.service.grpc import ZmqClient
from gnes.service.router import RouterService


class TestProto(unittest.TestCase):

    def setUp(self):
        self.dirname = os.path.dirname(__file__)
        self.publish_router_yaml = os.path.join(self.dirname, 'yaml', 'router-publish.yml')
        self.batch_router_yaml = os.path.join(self.dirname, 'yaml', 'router-batch.yml')
        self.reduce_router_yaml = os.path.join(self.dirname, 'yaml', 'router-reduce.yml')

    def test_service_empty(self):
        args = set_router_service_parser().parse_args([])
        with RouterService(args):
            pass

    def test_map_router(self):
        args = set_router_service_parser().parse_args([
            '--yaml_path', self.batch_router_yaml,
        ])
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in),
        ])
        with RouterService(args), ZmqClient(c_args) as c1:
            msg = gnes_pb2.Message()
            msg.request.index.docs.extend([gnes_pb2.Document() for _ in range(5)])
            c1.send_message(msg)
            r = c1.recv_message()
            self.assertEqual(len(r.request.index.docs), 2)
            r = c1.recv_message()
            self.assertEqual(len(r.request.index.docs), 2)
            r = c1.recv_message()
            self.assertEqual(len(r.request.index.docs), 1)

    def test_publish_router(self):
        args = set_router_service_parser().parse_args([
            '--yaml_path', self.publish_router_yaml,
            '--socket_out', str(SocketType.PUB_BIND)
        ])
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in),
            '--socket_in', str(SocketType.SUB_CONNECT)
        ])
        with RouterService(args), ZmqClient(c_args) as c1, ZmqClient(c_args) as c2:
            msg = gnes_pb2.Message()
            msg.request.index.docs.extend([gnes_pb2.Document() for _ in range(5)])
            c1.send_message(msg)
            r = c1.recv_message()
            self.assertEqual(r.envelope.num_part, 2)
            r = c2.recv_message()
            self.assertEqual(r.envelope.num_part, 2)

    def test_reduce_router(self):
        args = set_router_service_parser().parse_args([
            '--yaml_path', self.reduce_router_yaml,
            '--socket_out', str(SocketType.PUB_BIND)
        ])
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in),
            '--socket_in', str(SocketType.SUB_CONNECT)
        ])
        with RouterService(args), ZmqClient(c_args) as c1, ZmqClient(c_args) as c2:
            msg = gnes_pb2.Message()
            msg.request.index.docs.extend([gnes_pb2.Document() for _ in range(5)])
            msg.envelope.num_part = 3
            c1.send_message(msg)
            c1.send_message(msg)
            c1.send_message(msg)
            r = c1.recv_message()
            self.assertEqual(r.envelope.num_part, 1)
            print(r.envelope.routes)

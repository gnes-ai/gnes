import unittest

from gnes.cli.parser import set_frontend_parser


class TestParser(unittest.TestCase):
    def test_service_parser(self):
        args1 = set_frontend_parser().parse_args([])
        args2 = set_frontend_parser().parse_args([])
        self.assertNotEqual(args1.port_in, args2.port_in)
        self.assertNotEqual(args1.port_out, args2.port_out)

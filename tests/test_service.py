import unittest

from gnes.cli.parser import set_service_parser
from gnes.service.base import BaseService


class TestService(unittest.TestCase):
    def test_service_open_close(self):
        args = set_service_parser().parse_args([])
        with BaseService(args) as bs:
            bs.start()
            self.assertTrue(bs.is_ready)

        self.assertRaises(TimeoutError, lambda: bs.is_ready)

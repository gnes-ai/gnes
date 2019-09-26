import copy
import os
import time
import unittest

from gnes.cli.api import healthcheck
from gnes.cli.parser import set_router_parser, set_healthcheck_parser
from gnes.service.base import ServiceManager
from gnes.service.router import RouterService


class TestHealthCheck(unittest.TestCase):

    def test_health_check(self):
        a = set_router_parser().parse_args([
            '--yaml_path', 'BaseRouter',
        ])
        a1 = copy.deepcopy(a)
        b = set_healthcheck_parser().parse_args([
            '--port', str(a.port_ctrl)
        ])

        # before - fail
        with self.assertRaises(SystemExit) as cm:
            healthcheck(b)

        self.assertEqual(cm.exception.code, 1)

        # running - success
        with self.assertRaises(SystemExit) as cm:
            with RouterService(a):
                time.sleep(2)
                healthcheck(b)
        self.assertEqual(cm.exception.code, 0)

        # running - managerservice - success
        with self.assertRaises(SystemExit) as cm:
            with ServiceManager(RouterService, a1):
                time.sleep(2)
                healthcheck(b)
        self.assertEqual(cm.exception.code, 0)

        # after - fail
        with self.assertRaises(SystemExit) as cm:
            healthcheck(b)

        self.assertEqual(cm.exception.code, 1)

    @unittest.SkipTest
    def test_hc_os_env(self):
        os.environ['GNES_CONTROL_PORT'] = str(56789)
        a = set_router_parser().parse_args([
            '--yaml_path', 'BaseRouter',
        ])
        a1 = copy.deepcopy(a)
        b = set_healthcheck_parser().parse_args([
            '--port', os.environ.get('GNES_CONTROL_PORT')
        ])

        # before - fail
        with self.assertRaises(SystemExit) as cm:
            healthcheck(b)

        self.assertEqual(cm.exception.code, 1)

        # running - success
        with self.assertRaises(SystemExit) as cm:
            with RouterService(a):
                time.sleep(2)
                healthcheck(b)
        self.assertEqual(cm.exception.code, 0)

        # running - managerservice - success
        with self.assertRaises(SystemExit) as cm:
            with ServiceManager(RouterService, a1):
                time.sleep(2)
                healthcheck(b)
        self.assertEqual(cm.exception.code, 0)

        # after - fail
        with self.assertRaises(SystemExit) as cm:
            healthcheck(b)

        self.assertEqual(cm.exception.code, 1)
        os.unsetenv('GNES_CONTROL_PORT')

import os
import unittest

from gnes.cli.parser import set_composer_parser
from gnes.composer.base import YamlGraph


class TestCompose(unittest.TestCase):
    def setUp(self):
        self.dirname = os.path.dirname(__file__)
        self.html_path = os.path.join(self.dirname, 'test.html')

    def test_all(self):
        paths = [os.path.join(self.dirname, 'yaml', 'topology%d.yml' % j) for j in range(1, 8)]
        b_a = [(3, 3), (4, 4), (4, 5), (4, 7), (4, 6), (4, 8), (4, 9)]
        for p, j in zip(paths, b_a):
            self._test_topology(p, *j)

    def _test_topology(self, yaml_path: str, num_layer_before: int, num_layer_after: int):
        args = set_composer_parser().parse_args([
            '--yaml_path', yaml_path,
            '--html_path', self.html_path
        ])
        a = YamlGraph(args)
        self.assertEqual(len(a._layers), num_layer_before)
        r = a.build_layers()
        self.assertEqual(len(r), num_layer_after)
        for c in r:
            print(c)
        a.build_all()
        print(a.build_shell(r))
        os.path.exists(self.html_path)
        print(a.build_dockerswarm(r))

    # def tearDown(self):
    #     if os.path.exists(self.html_path):
    #         os.remove(self.html_path)

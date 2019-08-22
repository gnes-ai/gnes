import os
import unittest

from gnes.cli.parser import set_composer_parser, set_composer_flask_parser
from gnes.composer.base import YamlComposer
from gnes.composer.flask import YamlComposerFlask
from gnes.composer.http import YamlComposerHttp


class TestCompose(unittest.TestCase):
    def setUp(self):
        self.dirname = os.path.dirname(__file__)
        self.html_path = os.path.join(self.dirname, 'test.html')

    def test_all(self):
        paths = [os.path.join(self.dirname, 'yaml', 'topology%d.yml' % j) for j in range(1, 8)]
        b_a = [(3, 3), (4, 4), (4, 5), (4, 7), (4, 6), (4, 8), (4, 8)]
        for p, j in zip(paths, b_a):
            self._test_topology(p, *j)

    def _test_topology(self, yaml_path: str, num_layer_before: int, num_layer_after: int):
        args = set_composer_parser().parse_args([
            '--yaml_path', yaml_path,
            '--html_path', self.html_path
        ])
        a = YamlComposer(args)
        self.assertEqual(len(a._layers), num_layer_before)
        r = a.build_layers()
        self.assertEqual(len(r), num_layer_after)
        for c in r:
            print(c)
        a.build_all()
        print(a.build_shell(r))
        os.path.exists(self.html_path)
        print(a.build_dockerswarm(r))

    @unittest.SkipTest
    def test_http_local(self):
        args = set_composer_flask_parser().parse_args(['--serve'])
        YamlComposerHttp(args).run()

    @unittest.SkipTest
    def test_flask_local(self):
        args = set_composer_flask_parser().parse_args(['--flask'])
        YamlComposerFlask(args).run()

    def test_flask(self):
        yaml_path = os.path.join(self.dirname, 'yaml', 'topology1.yml')
        args = set_composer_flask_parser().parse_args([
            '--flask',
            '--yaml_path', yaml_path,
            '--html_path', self.html_path
        ])
        app = YamlComposerFlask(args)._create_flask_app().test_client()
        response = app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        response = app.post('/generate', follow_redirects=True)
        self.assertEqual(response.status_code, 406)

        response = app.post('/generate', data={'yaml-config': ''},
                            follow_redirects=True)
        self.assertEqual(response.status_code, 400)

        response = app.post('/generate',
                            data={'yaml-config': 'port: 5566\nservices:\n- name: Preprocessor\n- name: Encoder'},
                            follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        response = app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        if os.path.exists(self.html_path):
            os.remove(self.html_path)

import os
import unittest

import ruamel.yaml


class TestYaml(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        module_path = os.path.join(dirname, 'contrib', 'toy22.py')
        cls_name = 'FooContribEncoder'
        os.environ['GNES_CONTRIB_MODULE'] = '%s:%s' % (cls_name, module_path)
        self.yaml_path = os.path.join(os.path.dirname(__file__),
                                      'contrib', 'toy22.yml')

    def test_broken_contrib(self):
        os.environ['GNES_CONTRIB_MODULE'] = ''
        from gnes.encoder.base import BaseEncoder

        self.assertRaises(ruamel.yaml.constructor.ConstructorError, BaseEncoder.load_yaml, self.yaml_path)

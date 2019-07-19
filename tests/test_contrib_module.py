import os
import unittest


class TestYaml(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        module_path = os.path.join(dirname, 'contrib', 'dummy_contrib.py')
        cls_name = 'FooContribEncoder'
        os.environ['GNES_CONTRIB_MODULE'] = '%s:%s' % (cls_name, module_path)
        self.yaml_path = os.path.join(os.path.dirname(__file__),
                                      'contrib', 'dummy.yml')

    def test_load_contrib(self):
        from gnes.encoder.base import BaseEncoder, BaseTextEncoder
        a = BaseEncoder.load_yaml(self.yaml_path)
        self.assertIsInstance(a, BaseTextEncoder)
        self.assertEqual(a.encode([]), 'hello 531')

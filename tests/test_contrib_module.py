import os
import unittest.mock

dirname = os.path.dirname(__file__)
module_path = os.path.join(dirname, 'contrib', 'dummy_contrib.py')


@unittest.SkipTest
class TestContribModule(unittest.TestCase):
    def setUp(self):
        self.yaml_path = os.path.join(os.path.dirname(__file__),
                                      'contrib', 'dummy.yml')
        self.dump_yaml_path = os.path.join(os.path.dirname(__file__),
                                           'dummy-dump.yml')

    def tearDown(self):
        # reload gnes module on every unit test
        if os.path.exists(self.dump_yaml_path):
            os.remove(self.dump_yaml_path)

    def test_load_contrib(self):
        os.environ['GNES_CONTRIB_MODULE'] = module_path
        from gnes.encoder.base import BaseEncoder, BaseTextEncoder
        a = BaseEncoder.load_yaml(self.yaml_path)
        self.assertIsInstance(a, BaseTextEncoder)
        self.assertEqual(a.encode([]), 'hello 531')
        a.dump()
        a.dump_yaml(self.dump_yaml_path)
        b = BaseEncoder.load_yaml(self.dump_yaml_path)
        self.assertIsInstance(b, BaseTextEncoder)
        self.assertEqual(b.encode([]), 'hello 531')

    def test_bad_name(self):
        os.environ['GNES_CONTRIB_MODULE'] = module_path
        try:
            from gnes.encoder.base import BaseEncoder
        except AttributeError:
            pass

    def test_bad_path(self):
        os.environ['GNES_CONTRIB_MODULE'] = 'blah'
        try:
            from gnes.encoder.base import BaseEncoder
        except AttributeError:
            pass

import os
import sys
import unittest.mock

dirname = os.path.dirname(__file__)
module_path = os.path.join(dirname, 'contrib', 'dummy_contrib.py')
cls_name = 'FooContribEncoder'

@unittest.SkipTest
class TestContribModule(unittest.TestCase):
    def setUp(self):
        self.yaml_path = os.path.join(os.path.dirname(__file__),
                                      'contrib', 'dummy.yml')

    def tearDown(self):
        # reload gnes module on every unit test
        for mod in list(sys.modules.keys()):
            if mod.startswith('gnes.'):
                del (sys.modules[mod])

    @unittest.mock.patch.dict(os.environ, {'GNES_CONTRIB_MODULE': '%s:%s' % (cls_name, module_path)})
    def test_load_contrib(self):

        from gnes.encoder.base import BaseEncoder, BaseTextEncoder
        a = BaseEncoder.load_yaml(self.yaml_path)
        self.assertIsInstance(a, BaseTextEncoder)
        self.assertEqual(a.encode([]), 'hello 531')

    @unittest.mock.patch.dict(os.environ, {'GNES_CONTRIB_MODULE': '%s:%s' % ('blah', module_path)})
    def test_bad_name(self):
        try:
            from gnes.encoder.base import BaseEncoder
        except AttributeError:
            pass

    @unittest.mock.patch.dict(os.environ, {'GNES_CONTRIB_MODULE': '%s:%s' % (cls_name, 'blah')})
    def test_bad_path(self):
        try:
            from gnes.encoder.base import BaseEncoder
        except AttributeError:
            pass

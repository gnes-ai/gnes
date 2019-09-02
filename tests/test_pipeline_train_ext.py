import os
import unittest

from gnes.encoder.base import BaseEncoder
from gnes.helper import PathImporter


class TestPipeTrain(unittest.TestCase):
    def setUp(self):
        self.dirname = os.path.dirname(__file__)
        PathImporter.add_modules(*('{0}/contrib/dummy2.py,{0}/contrib/dummy3.py'.format(self.dirname).split(',')))

    def tearDown(self):
        if os.path.exists('dummy-pipeline.bin'):
            os.remove('dummy-pipeline.bin')
        if os.path.exists('dummy-pipeline.yml'):
            os.remove('dummy-pipeline.yml')

    def test_load_yaml(self):
        p = BaseEncoder.load_yaml(os.path.join(self.dirname, 'yaml', 'pipeline-multi-encoder2.yml'))
        self.assertFalse(p.is_trained)
        self.assertRaises(RuntimeError, p.encode, 1)
        p.train(1)
        self.assertTrue(p.is_trained)
        self.assertEqual(5, p.encode(1))
        p = BaseEncoder.load_yaml(os.path.join(self.dirname, 'yaml', 'pipeline-multi-encoder2.yml'))
        self.assertRaises(RuntimeError, p.encode, 1)

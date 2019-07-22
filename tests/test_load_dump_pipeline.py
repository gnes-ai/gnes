import os
import unittest

from gnes.encoder.base import BaseEncoder


class TestLoadDumpPipeline(unittest.TestCase):
    def setUp(self):
        self.dirname = os.path.dirname(__file__)
        self.yaml_path = os.path.join(self.dirname, 'yaml', 'dummy-pipeline.yml')
        self.dump_path = os.path.join(self.dirname, 'dummy-pipeline.bin')

    def test_base(self):
        a = BaseEncoder.load_yaml(self.yaml_path)
        self.assertFalse(a.is_trained)
        # simulate training
        a.is_trained = True
        a.dump()
        os.path.exists(self.dump_path)

        # load the dump from yaml
        b = BaseEncoder.load_yaml(self.yaml_path)
        self.assertTrue(b.is_trained)

    def tearDown(self):
        os.remove(self.dump_path)

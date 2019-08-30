import os
import unittest

from gnes.encoder.base import BaseEncoder, PipelineEncoder
from gnes.helper import train_required


class DummyEncoder(BaseEncoder):

    def train(self, *args, **kwargs):
        pass

    @train_required
    def encode(self, x):
        return x + 1


class TestPipeTrain(unittest.TestCase):
    def test_train(self):
        de = DummyEncoder()
        self.assertRaises(RuntimeError, de.encode, 1)
        de.train()
        self.assertEqual(2, de.encode(1))

    def tearDown(self):
        if os.path.exists('dummy-pipeline.bin'):
            os.remove('dummy-pipeline.bin')
        if os.path.exists('dummy-pipeline.yml'):
            os.remove('dummy-pipeline.yml')

    def test_pipeline_train(self):
        p = PipelineEncoder()
        p.components = lambda: [DummyEncoder(), DummyEncoder(), DummyEncoder()]
        self.assertRaises(RuntimeError, p.encode, 1)
        p.train(1)
        self.assertEqual(4, p.encode(1))
        p.name = 'dummy-pipeline'
        p.dump()
        p.dump_yaml()
        a = BaseEncoder.load_yaml(p.yaml_full_path)
        self.assertEqual(4, a.encode(1))

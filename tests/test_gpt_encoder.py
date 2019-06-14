import os
import unittest
import numpy as np
from numpy.testing import assert_array_equal

from gnes.encoder.gpt import GPTEncoder
from gnes.encoder.base import PipelineEncoder


class TestGPTEncoder(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'gpt_encoder.bin')
        self.gpt_path = os.path.join(dirname, 'yaml', 'gpt-binary-encoder.yml')

        self.test_str = []
        with open(os.path.join(dirname, 'sonnets.txt')) as f:
            for line in f:
                line = line.strip()
                if line:
                    self.test_str.append(line)

    def test_encoding(self):
        _encoder = GPTEncoder(
            model_dir=os.environ.get('GPT_CI_MODEL', '/openai_gpt'),
            pooling_strategy="REDUCE_MEAN")
        vec = _encoder.encode(self.test_str)
        self.assertEqual(vec.shape[0], len(self.test_str))
        self.assertEqual(vec.shape[1], 768)

        num_bytes = 8

        gpt = PipelineEncoder.load_yaml(self.gpt_path)
        self.assertRaises(RuntimeError, gpt.encode, self.test_str)

        gpt.train(self.test_str)
        out = gpt.encode(self.test_str)
        gpt.close()
        self.assertEqual(np.ndarray, type(out))
        self.assertEqual(num_bytes, out.shape[1])
        self.assertEqual(len(self.test_str), len(out))

        gpt.dump(self.dump_path)
        self.assertTrue(os.path.exists(self.dump_path))
        gpt2 = PipelineEncoder.load(self.dump_path)
        out2 = gpt2.encode(self.test_str)
        assert_array_equal(out, out2)

    def tearDown(self):
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)
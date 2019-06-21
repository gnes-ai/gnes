import os
import unittest

from gnes.encoder.text.gpt import GPTEncoder


# from numpy.testing import assert_array_equal


class TestGPTEncoder(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'gpt_encoder.bin')
        self.test_str = []
        with open(os.path.join(dirname, 'sonnets.txt')) as f:
            for line in f:
                line = line.strip()
                if line:
                    self.test_str.append(line)

        self.gpt_encoder = GPTEncoder(
            model_dir=os.environ.get('GPT_CI_MODEL', '/openai_gpt'),
            pooling_strategy="REDUCE_MEAN")

    def test_encoding(self):

        vec = self.gpt_encoder.encode(self.test_str)
        self.assertEqual(vec.shape[0], len(self.test_str))
        self.assertEqual(vec.shape[1], 768)

    def test_dump_load(self):
        self.gpt_encoder.dump(self.dump_path)
        gpt_encoder2 = GPTEncoder.load(self.dump_path)

        vec = gpt_encoder2.encode(self.test_str)
        self.assertEqual(vec.shape[0], len(self.test_str))
        self.assertEqual(vec.shape[1], 768)

    def tearDown(self):
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)
import os
import unittest

from gnes.encoder.text.gpt import GPT2Encoder


class TestGPT2Encoder(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'gpt2_encoder.bin')
        self.gpt_path = os.path.join(dirname, 'yaml',
                                     'gpt2-binary-encoder.yml')
        self.test_str = []
        with open(os.path.join(dirname, 'sonnets.txt')) as f:
            for line in f:
                line = line.strip()
                if line:
                    self.test_str.append(line)

        self.gpt2_encoder = GPT2Encoder(
            model_dir=os.environ.get('GPT2_CI_MODEL', '/openai_gpt2'),
            pooling_strategy="REDUCE_MEAN")

    def test_encoding(self):

        vec = self.gpt2_encoder.encode(self.test_str)
        self.assertEqual(vec.shape[0], len(self.test_str))
        self.assertEqual(vec.shape[1], 768)

    def test_dump_load(self):
        self.gpt2_encoder.dump(self.dump_path)

        gpt2_encoder2 = GPT2Encoder.load(self.dump_path)
        vec = self.gpt2_encoder.encode(self.test_str)
        self.assertEqual(vec.shape[0], len(self.test_str))
        self.assertEqual(vec.shape[1], 768)

    def tearDown(self):
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)

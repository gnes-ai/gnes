import os
import unittest

from gnes.encoder.text.flair import FlairEncoder


class TestFlairEncoder(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'flair_encoder.bin')

        self.test_str = []
        with open(os.path.join(dirname, 'sonnets.txt')) as f:
            for line in f:
                line = line.strip()
                if line:
                    self.test_str.append(line)

        self.flair_encoder = FlairEncoder(model_name=os.environ.get('FLAIR_CI_MODEL'))

    @unittest.SkipTest
    def test_encoding(self):
        vec = self.flair_encoder.encode(self.test_str[:2])
        print(vec.shape)
        self.assertEqual(vec.shape[0], 2)
        self.assertEqual(vec.shape[1], 4196)

    @unittest.SkipTest
    def test_dump_load(self):
        self.flair_encoder.dump(self.dump_path)

        flair_encoder2 = FlairEncoder.load(self.dump_path)
        vec = flair_encoder2.encode(self.test_str)
        self.assertEqual(vec.shape[0], len(self.test_str))
        self.assertEqual(vec.shape[1], 512)

    def tearDown(self):
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)

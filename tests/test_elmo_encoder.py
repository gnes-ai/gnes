import os
import unittest

from gnes.encoder.text.elmo import ElmoEncoder


@unittest.SkipTest
class TestElmoEncoder(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'elmo_encoder.bin')

        self.test_str = []
        with open(os.path.join(dirname, 'tangshi.txt')) as f:
            for line in f:
                line = line.strip()
                if line:
                    self.test_str.append(line)

        self.elmo_encoder = ElmoEncoder(
            model_dir=os.environ.get('ELMO_CI_MODEL', '/zhs.model'),
            pooling_strategy="REDUCE_MEAN")

    def test_encoding(self):
        vec = self.elmo_encoder.encode(self.test_str)
        self.assertEqual(vec.shape[0], len(self.test_str))
        self.assertEqual(vec.shape[1], 1024)

    def test_dump_load(self):
        self.elmo_encoder.dump(self.dump_path)

        elmo_encoder2 = ElmoEncoder.load(self.dump_path)

        vec = elmo_encoder2.encode(self.test_str)
        self.assertEqual(vec.shape[0], len(self.test_str))
        self.assertEqual(vec.shape[1], 1024)

    def tearDown(self):
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)

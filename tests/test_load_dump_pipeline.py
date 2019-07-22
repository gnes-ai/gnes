import os
import unittest

from gnes.encoder.base import BaseEncoder, PipelineEncoder


class DummyTFEncoder(BaseEncoder):
    def post_init(self):
        import tensorflow as tf
        self.a = tf.get_variable(name='a', shape=[])
        self.sess = tf.Session()

    def encode(self, a, *args):
        return self.sess.run(self.a + 1, feed_dict={self.a: a})


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

    def test_dummytf(self):
        d1 = DummyTFEncoder()
        self.assertEqual(d1.encode(1), 2)

        d2 = DummyTFEncoder()
        self.assertEqual(d2.encode(2), 3)

        d3 = PipelineEncoder()
        d3.component = lambda: [d1, d2]
        self.assertEqual(d2.encode(1), 3)

    def tearDown(self):
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)

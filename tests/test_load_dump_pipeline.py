import os
import unittest

from gnes.encoder.base import BaseEncoder, PipelineEncoder


class DummyTFEncoder(BaseEncoder):
    is_trained = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def post_init(self):
        import tensorflow as tf
        with tf.Graph().as_default():
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

        for c in a.components:
            c.is_trained = True
        a.dump()
        os.path.exists(self.dump_path)

        # load the dump from yaml
        b = BaseEncoder.load_yaml(self.yaml_path)
        self.assertTrue(b.is_trained)

    def test_name_warning(self):
        d1 = DummyTFEncoder()
        d2 = DummyTFEncoder()
        d1.name = ''
        d2.name = ''
        d3 = PipelineEncoder()
        d3.components = lambda: [d1, d2]
        d3.name = 'dummy-pipeline'
        d3.work_dir = './'
        d3.dump()
        d3.dump_yaml()
        print('there should not be any warning after this line')
        BaseEncoder.load_yaml(d3.yaml_full_path)

    def test_dummytf(self):
        d1 = DummyTFEncoder()
        self.assertEqual(d1.encode(1), 2)
        self.assertTrue(d1.is_trained)
        d1.dump()
        d11 = BaseEncoder.load(d1.dump_full_path)
        self.assertTrue(d11.is_trained)

        d2 = DummyTFEncoder()
        self.assertEqual(d2.encode(2), 3)
        self.assertTrue(d2.is_trained)

        d3 = PipelineEncoder()
        d3.components = lambda: [d1, d2]
        self.assertEqual(d3.encode(1), 3)
        self.assertTrue(d3.is_trained)
        self.assertTrue(d3.components[0].is_trained)
        self.assertTrue(d3.components[1].is_trained)

        d3.dump()
        d31 = BaseEncoder.load(d3.dump_full_path)
        self.assertTrue(d3.is_trained)
        self.assertTrue(d31.components[0].is_trained)
        self.assertTrue(d31.components[1].is_trained)

        d3.work_dir = self.dirname
        d3.name = 'dummy-pipeline'
        d3.dump_yaml()
        d3.dump()

        d4 = PipelineEncoder.load(d3.dump_full_path)
        self.assertTrue(d4.is_trained)
        self.assertTrue(d4.components[0].is_trained)
        self.assertTrue(d4.components[1].is_trained)

        d4 = PipelineEncoder.load_yaml(d3.yaml_full_path)
        self.assertTrue(d4.is_trained)
        self.assertTrue(d4.components[0].is_trained)
        self.assertTrue(d4.components[1].is_trained)

        self.assertEqual(d4.encode(4), 6)

    def tearDown(self):
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)

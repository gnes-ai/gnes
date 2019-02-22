import unittest

from bert_serving.client import BertClient


class TestBertServing(unittest.TestCase):
    def test_tf(self):
        import tensorflow as tf
        print(tf.__version__)
        a = tf.constant(1, dtype=tf.int32)
        with tf.Session() as sess:
            self.assertEqual(sess.run(a), 1)

    def test_bert_client(self):
        bc = BertClient(timeout=2000)
        vec = bc.encode(['你好么？我很好', '你好么？我很好!但 我还没吃'])
        self.assertEqual(vec.shape[0], 2)
        self.assertEqual(vec.shape[1], 768)

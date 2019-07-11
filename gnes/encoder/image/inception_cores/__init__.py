from .inception_v4 import *
import tensorflow as tf
import numpy as np


class Inception:

    def __init__(self, x, y, model_dir):

        self.sess = tf.Session()
        inception_v4.default_image_size = x
        arg_scope = inception_utils.inception_arg_scope()
        inputs = tf.placeholder(tf.float32, (None, x, y, 3))

        with slim.arg_scope(arg_scope):
            self.logits, self.end_points = inception_v4(inputs,
                                                        is_training=False,
                                                        dropout_keep_prob=1.0)
        self.saver = tf.train.Saver()
        self.saver.restore(self.sess, model_dir)

    def encode(self, vecs, select_layer):

        _, end_points_ = sess.run((logits, end_points),
                                  feed_dict={inputs: vecs})
        res.append(end_points_[select_layer])
        return np.concatenate(res, axis=0).astype(np.float32)
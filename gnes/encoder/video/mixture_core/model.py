#  Tencent is pleased to support the open source community by making GNES available.
#
#  Copyright (C) 2019 THL A29 Limited, a Tencent company. All rights reserved.
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import math

import tensorflow as tf
import tensorflow.contrib.slim as slim


class NetFV:
    def __init__(self, feature_size,
                 cluster_size,
                 vocab_size,
                 method='netvlad',
                 use_length=False,
                 input_size=None,
                 use_2nd_label=False,
                 vocab_size_2=None,
                 add_batch_norm=True,
                 is_training=False,
                 use_weights=True,
                 save_dir=None,
                 multitask_method=None,
                 l2_penalty=1e-6):
        if input_size == None:
            self.input_size = feature_size
        else:
            self.input_size = input_size
        self.feature_size = feature_size
        self.use_length = use_length
        self.is_training = is_training
        self.vocab_size = vocab_size
        self.use_2nd_label = use_2nd_label
        self.vocab_size_2 = vocab_size_2
        self.add_batch_norm = add_batch_norm
        self.cluster_size = cluster_size
        self.use_weights = use_weights
        self.l2_penalty = l2_penalty
        self.method = method
        self.multitask_method = multitask_method
        self.build_model()
        self.build_loss()

    @staticmethod
    def rand_init(feature_size):
        return tf.random_normal_initializer(stddev=1 / math.sqrt(feature_size))

    def build_model(self):
        self.feeds = tf.placeholder(tf.float32, [None, None, self.input_size])
        self.feeds_length = tf.placeholder(tf.int32, [None])

        self.inputs = tf.layers.dense(self.feeds, self.feature_size)

        self.weights = tf.placeholder(tf.float32, [None, self.vocab_size])
        self.max_frames = tf.shape(self.inputs)[1]
        self.seq_length = tf.cast(tf.sequence_mask(self.feeds_length,
                                                   self.max_frames), tf.float32)
        if self.method == 'fvnet':
            self.build_fvnet()
        elif self.method == 'netvlad':
            self.build_netvlad()
        elif self.method == 'pooling':
            self.build_pooling()

    def build_pooling(self):
        self.repre = tf.layers.dense(self.inputs, self.feature_size)
        self.repre = tf.reduce_max(self.repre, axis=1)

    def build_fvnet(self):
        reshaped_input = tf.reshape(self.inputs, [-1, self.feature_size])
        cluster_weights = tf.get_variable("cluster_weights",
                                          [self.feature_size, self.cluster_size],
                                          initializer=NetFV.rand_init(self.feature_size))

        covar_weights = tf.get_variable("covar_weights",
                                        [self.feature_size, self.cluster_size],
                                        initializer=NetFV.rand_init(self.feature_size))

        covar_weights = tf.square(covar_weights)
        eps = tf.constant([1e-6])
        covar_weights = tf.add(covar_weights, eps)

        tf.summary.histogram("cluster_weights", cluster_weights)
        activation = tf.matmul(reshaped_input, cluster_weights)
        if self.add_batch_norm:
            activation = slim.batch_norm(activation,
                                         center=True,
                                         scale=True,
                                         is_training=self.is_training,
                                         scope="cluster_bn")
        else:
            cluster_biases = tf.get_variable("cluster_biases",
                                             [self.cluster_size],
                                             initializer=NetFV.rand_init(self.feature_size))
            tf.summary.histogram("cluster_biases", cluster_biases)
            activation += cluster_biases

        activation = tf.nn.softmax(activation)
        tf.summary.histogram("cluster_output", activation)

        activation = tf.reshape(activation, [-1, self.max_frames, self.cluster_size])

        a_sum = tf.reduce_sum(activation, -2, keepdims=True)

        cluster_weights2 = tf.scalar_mul(0.01, cluster_weights)

        a = tf.multiply(a_sum, cluster_weights2)

        activation = tf.transpose(activation, perm=[0, 2, 1])

        reshaped_input = tf.reshape(reshaped_input,
                                    [-1, self.max_frames, self.feature_size])
        fv1 = tf.matmul(activation, reshaped_input)

        fv1 = tf.transpose(fv1, perm=[0, 2, 1])

        # computing second order FV
        a2 = tf.multiply(a_sum, tf.square(cluster_weights2))

        b2 = tf.multiply(fv1, cluster_weights2)
        fv2 = tf.matmul(activation, tf.square(reshaped_input))

        fv2 = tf.transpose(fv2, perm=[0, 2, 1])
        fv2 = tf.add_n([a2, fv2, tf.scalar_mul(-2, b2)])

        fv2 = tf.divide(fv2, tf.square(covar_weights))
        fv2 = tf.subtract(fv2, a_sum)

        fv2 = tf.reshape(fv2, [-1, self.cluster_size * self.feature_size])
        fv2 = tf.nn.l2_normalize(fv2, 1)
        fv2 = tf.reshape(fv2, [-1, self.cluster_size * self.feature_size])
        fv2 = tf.nn.l2_normalize(fv2, 1)

        fv1 = tf.subtract(fv1, a)
        fv1 = tf.divide(fv1, covar_weights)
        fv1 = tf.nn.l2_normalize(fv1, 1)
        fv1 = tf.reshape(fv1, [-1, self.cluster_size * self.feature_size])
        fv1 = tf.nn.l2_normalize(fv1, 1)

        self.repre = tf.concat([fv1, fv2], 1)
        self.repre = tf.layers.dense(self.repre, self.feature_size)

    def build_netvlad(self):
        reshaped_input = tf.reshape(self.inputs, [-1, self.feature_size])
        cluster_weights = tf.get_variable("cluster_weights",
                                          [self.feature_size, self.cluster_size],
                                          initializer=NetFV.rand_init(self.feature_size))
        activation = tf.matmul(reshaped_input, cluster_weights)
        if self.add_batch_norm:
            activation = slim.batch_norm(activation,
                                         center=True,
                                         scale=True,
                                         is_training=self.is_training,
                                         scope="cluster_bn")
        else:
            cluster_biases = tf.get_variable("cluster_biases",
                                             [self.cluster_size],
                                             initializer=NetFV.rand_init(self.feature_size))
            activation += cluster_biases
        activation = tf.nn.softmax(activation)
        activation = tf.reshape(activation, [-1, self.max_frames, self.cluster_size])
        if self.use_length:
            activation *= tf.reshape(self.seq_length, [-1, self.max_frames, 1])

        a_sum = tf.reduce_sum(activation, -2, keep_dims=True)

        if self.use_length:
            a_sum = a_sum / tf.cast(tf.reshape(self.feeds_length, [-1, 1, 1]), tf.float32)

        cluster_weights2 = tf.get_variable("cluster_weights2",
                                           [1, self.feature_size, self.cluster_size],
                                           initializer=NetFV.rand_init(self.feature_size))

        a = tf.multiply(a_sum, cluster_weights2)
        activation = tf.transpose(activation, perm=[0, 2, 1])

        reshaped_input = tf.reshape(reshaped_input,
                                    [-1, self.max_frames, self.feature_size])
        vlad = tf.matmul(activation, reshaped_input)
        if self.use_length:
            vlad = vlad / tf.cast(tf.reshape(self.feeds_length, [-1, 1, 1]), tf.float32)
        vlad = tf.transpose(vlad, perm=[0, 2, 1])
        vlad = tf.subtract(vlad, a)

        vlad = tf.nn.l2_normalize(vlad, 1)

        vlad = tf.reshape(vlad, [-1, self.cluster_size * self.feature_size])
        vlad = tf.nn.l2_normalize(vlad, 1)
        self.repre = vlad

    def build_loss(self):
        self.probabilities = tf.layers.dense(self.repre,
                                             self.vocab_size,
                                             activation=tf.nn.tanh)
        self.probabilities = tf.layers.dense(self.probabilities, self.vocab_size)
        self.probabilities = tf.nn.softmax(self.probabilities)

        self.label = tf.placeholder(tf.int32, [None, self.vocab_size])
        logits = tf.cast(self.label, tf.float32)
        if self.use_weights:
            logits = logits * self.weights
        self.loss = - tf.log(tf.reduce_sum(logits * self.probabilities, axis=1) + 1e-9)
        self.loss = tf.reduce_mean(self.loss)
        self.pred = tf.argmax(self.probabilities, 1)
        self.avg_diff = tf.cast(tf.equal(tf.argmax(self.label, 1), self.pred), tf.float32)
        self.avg_diff = tf.reduce_mean(self.avg_diff)

        # add 2nd layer labels
        if self.use_2nd_label:
            self.label_2 = tf.placeholder(tf.int32, [None, self.vocab_size_2])
            logits2 = tf.cast(self.label_2, tf.float32)

            if self.multitask_method is None:
                self.probabilities2 = tf.layers.dense(self.repre,
                                                      self.vocab_size_2,
                                                      activation=tf.nn.tanh)
                self.probabilities2 = tf.layers.dense(self.probabilities2, self.vocab_size_2)
                self.probabilities2 = tf.nn.softmax(self.probabilities2)

            elif self.multitask_method == 'Attention':
                self.x = tf.get_variable('emb',
                                         shape=[self.vocab_size, self.feature_size],
                                         dtype=tf.float32,
                                         initializer=NetFV.rand_init(self.feature_size))
                self.emb_label = tf.matmul(self.probabilities, self.x)
                self.emb_concat = tf.concat([self.emb_label, self.repre], axis=1)
                self.probabilities2 = tf.layers.dense(self.emb_concat,
                                                      self.vocab_size_2,
                                                      activation=tf.nn.tanh)
                self.probabilities2 = tf.layers.dense(self.probabilities2,
                                                      self.vocab_size_2)
                self.probabilities2 = tf.nn.softmax(self.probabilities2)

            self.loss += tf.reduce_mean(-tf.log(
                tf.reduce_sum(logits2 * self.probabilities2, axis=1) + 1e-9))
            self.pred2 = tf.argmax(self.probabilities2, 1)
            self.avg_diff2 = tf.cast(tf.equal(tf.argmax(self.label_2, 1), self.pred2), tf.float32)
            self.avg_diff2 = tf.reduce_mean(self.avg_diff2)

        self.optimizer = tf.train.AdamOptimizer(learning_rate=0.0005,
                                                epsilon=1e-08,
                                                name='adam')
        self.train_op = slim.learning.create_train_op(self.loss, self.optimizer)
        self.eval_res = {'loss': self.loss, 'avg_diff': self.avg_diff}
        if self.use_2nd_label:
            self.eval_res['avg_diff2'] = self.avg_diff2

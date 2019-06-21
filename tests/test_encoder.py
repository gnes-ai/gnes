import os
import unittest

import numpy as np
from numpy.testing import assert_allclose

from gnes.encoder.base import PipelineEncoder
from gnes.encoder.numeric.pca import PCALocalEncoder
from gnes.encoder.numeric.pq import PQEncoder
from gnes.encoder.numeric.tf_pq import TFPQEncoder


class TestPCA(unittest.TestCase):
    def setUp(self):
        self.test_vecs = np.random.random([1000, 100]).astype('float32')
        dirname = os.path.dirname(__file__)
        self.lopq_yaml_np = os.path.join(dirname, 'yaml', 'lopq-encoder-2-np.yml')
        self.lopq_yaml_tf = os.path.join(dirname, 'yaml', 'lopq-encoder-2-tf.yml')
        self.lopq_yaml_np2 = os.path.join(dirname, 'yaml', 'lopq-encoder-3.yml')

    def test_pq_assert(self):
        self._test_pq_assert(PQEncoder)
        self._test_pq_assert(TFPQEncoder)

    def test_pq_tfpq_identity(self):
        def _test_pq_tfpq_identity(pq1, pq2):
            pq1.train(self.test_vecs)
            out1 = pq1.encode(self.test_vecs)
            pq2._copy_from(pq1)
            out2 = pq2.encode(self.test_vecs)
            assert_allclose(out1, out2)

        _test_pq_tfpq_identity(PQEncoder(10), TFPQEncoder(10))
        _test_pq_tfpq_identity(TFPQEncoder(10), PQEncoder(10))

    def _test_pq_assert(self, cls):
        self.assertRaises(AssertionError, cls, 100, 0)
        self.assertRaises(AssertionError, cls, 100, 256)

        pq = cls(8)
        self.assertRaises(AssertionError, pq.train, self.test_vecs)

        pq = cls(101)
        self.assertRaises(AssertionError, pq.train, self.test_vecs)

    def _simple_assert(self, out, num_bytes, num_clusters):
        self.assertEqual(bytes, type(out))
        self.assertEqual(self.test_vecs.shape[0] * num_bytes, len(out))
        self.assertTrue(np.all(np.frombuffer(out, np.uint8) <= num_clusters))

    def test_assert_pca(self):
        self.assertRaises(AssertionError, PCALocalEncoder, 8, 3)
        self.assertRaises(AssertionError, PCALocalEncoder, 2, 3)

        pca = PCALocalEncoder(100, 2)
        self.assertRaises(AssertionError, pca.train, self.test_vecs)

        pca = PCALocalEncoder(8, 2)
        self.assertRaises(AssertionError, pca.train, self.test_vecs[:7])

        pca.train(self.test_vecs)
        out = pca.encode(self.test_vecs)
        self.assertEqual(out.shape[1], 8)
        self.assertEqual(out.shape[0], self.test_vecs.shape[0])

    def test_train_pca(self):
        num_bytes = 8
        num_clusters = 11
        lopq = PipelineEncoder.load_yaml(self.lopq_yaml_np2)
        lopq.train(self.test_vecs)
        out = lopq.encode(self.test_vecs)
        self._simple_assert(out, num_bytes, num_clusters)

    # def test_train_pca_assert(self):
    #     # from PCA
    #     self.assertRaises(AssertionError, LOPQEncoder, num_bytes=100, pca_output_dim=20)
    #     # from PCA
    #     self.assertRaises(AssertionError, LOPQEncoder, num_bytes=7, pca_output_dim=20)
    #     # from LOPQ, cluster too large
    #     self.assertRaises(AssertionError, LOPQEncoder, num_bytes=4, pca_output_dim=20, cluster_per_byte=256)

    def test_encode_backend(self):
        num_bytes = 8
        lopq = PipelineEncoder.load_yaml(self.lopq_yaml_tf)
        lopq.train(self.test_vecs)
        out = lopq.encode(self.test_vecs)
        self._simple_assert(out, num_bytes, 255)

        lopq2 = PipelineEncoder.load_yaml(self.lopq_yaml_np)
        lopq2.train(self.test_vecs)
        out = lopq2.encode(self.test_vecs)
        self._simple_assert(out, num_bytes, 255)

        # copy from lopq
        lopq2._copy_from(lopq)
        out2 = lopq2.encode(self.test_vecs)
        self._simple_assert(out, num_bytes, 255)

        self.assertEqual(out, out2)

    def test_encode_batching(self):
        num_bytes = 8
        lopq = PipelineEncoder.load_yaml(self.lopq_yaml_tf)
        lopq.train(self.test_vecs)
        out = lopq.encode(self.test_vecs, batch_size=32)
        self._simple_assert(out, num_bytes, 255)
        out2 = lopq.encode(self.test_vecs, batch_size=64)
        self.assertEqual(out, out2)

    # def test_num_cluster(self):
    #     def _test_num_cluster(num_bytes, num_cluster, backend):
    #         lopq = LOPQEncoder(num_bytes,
    #                            cluster_per_byte=num_cluster,
    #                            pca_output_dim=20, pq_backend=backend)
    #         lopq.train(self.test_vecs)
    #         out = lopq.encode(self.test_vecs)
    #         self._simple_assert(out, num_bytes, num_cluster)
    #
    #     _test_num_cluster(10, 3, 'numpy')
    #     _test_num_cluster(10, 3, 'tensorflow')
    #     _test_num_cluster(10, 5, 'numpy')
    #     _test_num_cluster(10, 5, 'tensorflow')

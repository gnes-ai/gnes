import unittest

import numpy as np

from src.nes.encoder.lopq import LOPQEncoder
from src.nes.encoder.pq import PQEncoder
from src.nes.encoder.tf_pq import TFPQEncoder


class TestPCA(unittest.TestCase):
    def setUp(self):
        self.test_vecs = np.random.random([1000, 100])
        self.test_vecs = np.array(self.test_vecs, np.float32)

    def test_pq_assert(self):
        self._test_pq_assert(PQEncoder)
        self._test_pq_assert(TFPQEncoder)

    def test_pq_tfpq_identity(self):
        def _test_pq_tfpq_identity(pq1, pq2):
            pq1.train(self.test_vecs)
            out1 = pq1.encode(self.test_vecs)
            pq2.copy_from(pq1)
            out2 = pq2.encode(self.test_vecs)
            self.assertEqual(out1, out2)

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

    def test_train_no_pca(self):
        num_bytes = 10
        num_clusters = 11
        lopq = LOPQEncoder(num_bytes, cluster_per_byte=num_clusters)
        lopq.train(self.test_vecs)
        out = lopq.encode(self.test_vecs)
        self._simple_assert(out, num_bytes, num_clusters)

    def test_train_pca(self):
        num_bytes = 10
        num_clusters = 11
        lopq = LOPQEncoder(num_bytes, cluster_per_byte=num_clusters, pca_output_dim=20)
        lopq.train(self.test_vecs)
        out = lopq.encode(self.test_vecs)
        self._simple_assert(out, num_bytes, num_clusters)

    def test_train_pca_assert(self):
        # from PCA
        num_bytes = 100
        lopq = LOPQEncoder(num_bytes, pca_output_dim=20)
        self.assertRaises(AssertionError, lopq.train, self.test_vecs)
        # from PCA
        num_bytes = 7
        lopq = LOPQEncoder(num_bytes, pca_output_dim=20)
        self.assertRaises(AssertionError, lopq.train, self.test_vecs)
        # from LOPQ, cluster too large
        self.assertRaises(AssertionError, LOPQEncoder, num_bytes, cluster_per_byte=256)

    #
    # def test_encode(self):
    #     lopq = LOPQEncoder(self.num_bytes, self.dim_per_bytes)
    #     lopq.train(self.test_vecs)
    #     out = lopq.encode(self.test_vecs)
    #     self.assertEqual(bytes, type(out))
    #     self.assertEqual(self.test_vecs.shape[0] * int(self.num_bytes / self.dim_per_bytes),
    #                      len(out))
    #
    # def test_copy_from(self):
    #     lopq1 = LOPQEncoder(self.num_bytes, self.dim_per_bytes, backend='tensorflow')
    #     lopq1.train(self.test_vecs)
    #     out1 = lopq1.encode(self.test_vecs)
    #
    #     lopq2 = LOPQEncoder(self.num_bytes, self.dim_per_bytes, backend='tensorflow')
    #     lopq2.copy_from(lopq1)
    #     out2 = lopq2.encode(self.test_vecs)
    #
    #     self.assertEqual(out1, out2)
    #
    # def test_encode_backend(self):
    #     lopq = LOPQEncoder(self.num_bytes, self.dim_per_bytes, backend='tensorflow')
    #     lopq.train(self.test_vecs)
    #     out = lopq.encode(self.test_vecs[:10])
    #     self.assertEqual(10 * int(self.num_bytes / self.dim_per_bytes), len(out))
    #     self.assertEqual(bytes, type(out))
    #
    #     lopq2 = LOPQEncoder(self.num_bytes, self.dim_per_bytes, backend='numpy')
    #     # copy from lopq
    #     lopq2.copy_from(lopq)
    #     out2 = lopq2.encode(self.test_vecs[:10])
    #     self.assertEqual(10 * int(self.num_bytes / self.dim_per_bytes), len(out2))
    #     self.assertEqual(bytes, type(out2))
    #
    #     self.assertEqual(out, out2)
    #
    # def test_encode_batching(self):
    #     lopq = LOPQEncoder(self.num_bytes, self.dim_per_bytes, backend='tensorflow')
    #     lopq.train(self.test_vecs)
    #     out = lopq.encode(self.test_vecs, batch_size=32)
    #     self.assertEqual(self.test_vecs.shape[0] * int(self.num_bytes / self.dim_per_bytes), len(out))
    #     self.assertEqual(bytes, type(out))
    #     out2 = lopq.encode(self.test_vecs, batch_size=64)
    #     self.assertEqual(out, out2)


if __name__ == '__main__':
    unittest.main()

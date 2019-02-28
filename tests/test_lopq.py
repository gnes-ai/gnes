import unittest

import numpy as np

from src.nes.encoder.lopq import LOPQEncoder


class TestPCA(unittest.TestCase):
    def setUp(self):
        self.num_bytes = 40
        self.dim_per_bytes = 5
        self.test_vecs = np.random.random([1000, 120])
        self.test_vecs = np.array(self.test_vecs, np.float32)

    def test_train(self):
        lopq = LOPQEncoder(self.num_bytes, self.dim_per_bytes)
        lopq.train(self.test_vecs)

    def test_encode(self):
        lopq = LOPQEncoder(self.num_bytes, self.dim_per_bytes)
        lopq.train(self.test_vecs)
        out = lopq.encode(self.test_vecs)
        self.assertEqual(bytes, type(out))
        self.assertEqual(self.test_vecs.shape[0] * int(self.num_bytes / self.dim_per_bytes),
                         len(out))

    def test_copy_from(self):
        lopq1 = LOPQEncoder(self.num_bytes, self.dim_per_bytes, backend='tensorflow')
        lopq1.train(self.test_vecs)
        out1 = lopq1.encode(self.test_vecs)

        lopq2 = LOPQEncoder(self.num_bytes, self.dim_per_bytes, backend='tensorflow')
        lopq2.copy_from(lopq1)
        out2 = lopq2.encode(self.test_vecs)

        self.assertEqual(out1, out2)

    def test_encode_backend(self):
        lopq = LOPQEncoder(self.num_bytes, self.dim_per_bytes, backend='tensorflow')
        lopq.train(self.test_vecs)
        out = lopq.encode(self.test_vecs[:10])
        self.assertEqual(10 * int(self.num_bytes / self.dim_per_bytes), len(out))
        self.assertEqual(bytes, type(out))

        lopq2 = LOPQEncoder(self.num_bytes, self.dim_per_bytes, backend='numpy')
        # copy from lopq
        lopq2.copy_from(lopq)
        out2 = lopq2.encode(self.test_vecs[:10])
        self.assertEqual(10 * int(self.num_bytes / self.dim_per_bytes), len(out2))
        self.assertEqual(bytes, type(out2))

        self.assertEqual(out, out2)

    def test_encode_batching(self):
        lopq = LOPQEncoder(self.num_bytes, self.dim_per_bytes, backend='tensorflow')
        lopq.train(self.test_vecs)
        out = lopq.encode(self.test_vecs, batch_size=32)
        self.assertEqual(self.test_vecs.shape[0] * int(self.num_bytes / self.dim_per_bytes), len(out))
        self.assertEqual(bytes, type(out))
        out2 = lopq.encode(self.test_vecs, batch_size=64)
        self.assertEqual(out, out2)

    def test_num_clusters(self):
        lopq = LOPQEncoder(self.num_bytes, self.dim_per_bytes, cluster_per_byte=9)
        lopq.train(self.test_vecs)
        out = lopq.encode(self.test_vecs)
        # 0 is reserved for NULL cluster, then 1,2,...,9 for real cluster id
        self.assertTrue(np.all(np.frombuffer(out, np.uint8) <= 9))


if __name__ == '__main__':
    unittest.main()

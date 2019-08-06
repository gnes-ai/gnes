import unittest

import numpy as np
from numpy.testing import assert_array_equal

from gnes.encoder.base import BaseEncoder
from gnes.helper import batching, batch_iterator

get_batch_size = lambda x: 2


class bar(BaseEncoder):
    def __init__(self):
        super().__init__()
        self.batch_size = None

    @batching(batch_size=2, num_batch=4)
    def foo(self, data):
        return np.array(data)

    @batching(batch_size=2)
    def bar(self, data):
        return np.array(data)

    @batching(batch_size=8, num_batch=8)
    def foo1(self, data):
        return np.array(data)

    @batching
    def foo2(self, data):
        return np.array(data)

    @batching(batch_size=get_batch_size)
    def foo3(self, data):
        return np.array(data)

    @batching(batch_size=get_batch_size)
    def train(self, data):
        print('train: %s' % data)


class TestBatching(unittest.TestCase):
    def test_iterator(self):
        a = [1, 2, 3, 4, 5, 6, 7]
        b = np.array([[1, 2], [3, 4], [5, 6], [7, 8], [9, 10]])

        num_batches = np.ceil(len(a) / 2)
        act_batch = 0
        for j in batch_iterator(a, 2):
            self.assertLessEqual(len(j), 2)
            self.assertEqual(type(j), list)
            act_batch += 1
        self.assertEqual(num_batches, act_batch)

        num_batches = np.ceil(len(b) / 2)
        act_batch = 0
        for j in batch_iterator(b, 2):
            self.assertLessEqual(j.shape[0], 2)
            self.assertEqual(type(j), np.ndarray)
            act_batch += 1
        self.assertEqual(num_batches, act_batch)

        num_batches = np.ceil(len(a) / 2)
        act_batch = 0
        for j in batch_iterator(iter(a), 2):
            self.assertLessEqual(len(j), 2)
            act_batch += 1
        self.assertEqual(num_batches, act_batch)

    def test_decorator(self):
        b = bar()

        def _test_fn(fn):
            self.assertEqual(fn([1]), np.array([1, ]))
            self.assertSequenceEqual(fn([1, 2]).tolist(), [1, 2])
            self.assertSequenceEqual(fn(list(range(1, 30))).tolist(), list(range(1, 30)))
            self.assertSequenceEqual(fn(range(1, 30)).tolist(), list(range(1, 30)))

        _test_fn(b.foo1)
        _test_fn(b.foo2)
        _test_fn(b.bar)

        self.assertSequenceEqual(b.foo(range(1, 30)).tolist(), list(range(1, 9)))
        t = np.random.randint(0, 255, [32, 10])
        assert_array_equal(b.foo1(t), t)
        assert_array_equal(b.bar(t), t)
        assert_array_equal(b.foo(t), t[:8])

        b.batch_size = 8
        _test_fn(b.foo2)
        _test_fn(b.foo3)
        self.assertEqual(b.train([1]), None)

    def test_mini_batch(self):
        x = list(range(10))

        @batching(batch_size=4)
        def _do_mini_batch(_, y):
            return y

        # this will follow self.batch_size, which is None
        @batching
        def _do_mini_batch2(_, y):
            return y

        self.assertEqual(_do_mini_batch(None, x), [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9]])
        self.assertEqual(_do_mini_batch2(self, x), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

        self.batch_size = 4

        self.assertEqual(_do_mini_batch2(self, x), [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9]])

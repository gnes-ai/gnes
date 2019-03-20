import random
import unittest

import numpy as np

from gnes.helper import get_perm


class TestPartition(unittest.TestCase):

    def test_greedy_partition(self):
        l = 6
        # 6 must be dividable by 2 and 3, otherwise this unit test will fail as there is no
        # perfect partition
        x = np.array([random.random()] * l + [random.random()] * l)
        a = get_perm(x, 2)
        self.assertEqual(sum(x[a[:l]]), sum(x[a[l:]]))

        x = np.array([random.random()] * l + [random.random()] * l + [random.random()] * l)
        b = get_perm(x, 3)
        self.assertEqual(sum(x[b[:l]]), sum(x[b[l:(2 * l)]]))
        self.assertEqual(sum(x[b[:l]]), sum(x[b[(2 * l):]]))

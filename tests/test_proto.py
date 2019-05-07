import unittest

import numpy as np
from numpy.testing import assert_array_equal

from gnes.proto import array2blob, blob2array


class TestProto(unittest.TestCase):

    def test_array_proto(self):
        x = np.random.random([5, 4])
        blob = array2blob(x)
        x1 = blob2array(blob)
        assert_array_equal(x, x1)

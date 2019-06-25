import unittest

import numpy as np
from numpy.testing import assert_array_equal

from gnes.proto import gnes_pb2, array2blob, blob2array


class TestProto(unittest.TestCase):

    def test_array_proto(self):
        x = np.random.random([5, 4])
        blob = array2blob(x)
        x1 = blob2array(blob)
        assert_array_equal(x, x1)

    def test_new_msg(self):
        a = gnes_pb2.Message()
        a.response.index.status = gnes_pb2.Response.SUCCESS
        print(a)
        a.request.train.docs.extend([gnes_pb2.Document() for _ in range(2)])
        print(a)
        a.request.train.ClearField('docs')
        a.request.train.docs.extend([gnes_pb2.Document() for _ in range(3)])
        print(a)

import unittest

from google.protobuf.json_format import MessageToJson, Parse
from numpy.testing import assert_array_equal

from gnes.proto import *


class TestProto(unittest.TestCase):

    def test_array_proto(self):
        x = np.random.random([5, 4])
        blob = array2blob(x)
        x1 = blob2array(blob)
        assert_array_equal(x, x1)

    def test_new_msg(self):
        msg = new_message('test')
        print(msg)
        json_obj = MessageToJson(msg)
        print(json_obj)
        msg2 = Parse(json_obj, gnes_pb2.BaseMessage())
        print(msg2)
        self.assertEqual(msg, msg2)

        msg.envelope.routes[0].timestamp.seconds = 1
        self.assertNotEqual(msg, msg2)

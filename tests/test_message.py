import unittest

import numpy as np

from gnes.service import Message


class TestMessage(unittest.TestCase):
    def test_numpy(self):
        a = np.random.random([5, 3])
        m = Message(msg_content=a, client_id='123')
        print(m.content_type)
        np.testing.assert_almost_equal(a, m.msg_content)
        # test if use pointer
        a[0][0] = 1
        np.testing.assert_almost_equal(a, m.msg_content)
        b = np.random.random([4, 6])
        n = m.copy_mod(msg_content=b)
        self.assertNotEqual(m.msg_content, n.msg_content)
        self.assertNotEqual(m.content_type, n.content_type)
        self.assertEqual(m.client_id, n.client_id)

        a = 'adsa'
        m = Message(msg_content=a)
        print(m.content_type)
        self.assertEqual(a, m.msg_content)

        a = b'a23dsa'
        m = Message(msg_content=a)
        print(m.content_type)
        self.assertEqual(a.decode(), m.msg_content)

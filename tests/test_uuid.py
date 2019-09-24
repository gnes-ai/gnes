import unittest

from gnes.uuid import BaseIDGenerator, SnowflakeIDGenerator

class TestUUID(unittest.TestCase):
    def test_base_uuid(self):
        uuid_generator = BaseIDGenerator()
        last = -1
        for _ in range(10000):
            nid = uuid_generator.next()
            self.assertGreater(nid, last)
            last = nid


    def test_snoflake(self):
        uuid_generator = SnowflakeIDGenerator()
        last = -1
        for _ in range(10000):
            nid = uuid_generator.next()
            self.assertGreater(nid, last)
            last = nid

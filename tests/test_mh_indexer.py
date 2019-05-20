import os
import unittest

from gnes.indexer.base import BaseIndexer


class TestMHIndexer(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.yaml_path1 = os.path.join(dirname, 'yaml', 'base-indexer2.yml')
        self.yaml_path2 = os.path.join(dirname, 'yaml', 'base-indexer3.yml')

    def test_ind1(self):
        mhi = BaseIndexer.load_yaml(self.yaml_path1)
        print(mhi)

    def test_ind2(self):
        mhi = BaseIndexer.load_yaml(self.yaml_path2)
        print(mhi)

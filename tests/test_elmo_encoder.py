import os
import unittest
from shutil import rmtree

from gnes.document import UniSentDocument, MultiSentDocument
from gnes.encoder import PipelineEncoder
from gnes.encoder.elmo import ElmoEncoder


class TestElmoEncoder(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'elmo_encoder.bin')
        # self.bbe_path = os.path.join(dirname, 'yaml', 'bert-binary-encoder.yml')

        self.test_data1 = UniSentDocument.from_file(os.path.join(dirname, 'tangshi.txt'))
        self.test_data2 = MultiSentDocument.from_file(os.path.join(dirname, 'tangshi.txt'))
        self.test_str = [s for d in self.test_data1 for s in d.sentences]

        self.elmo_encoder = ElmoEncoder(model_dir=os.environ.get('ELMO_CI_MODEL', '/zhs_model'))


    def test_encoding(self):
        vec = self.elmo_encoder.encode(self.test_str)

        print(vec)

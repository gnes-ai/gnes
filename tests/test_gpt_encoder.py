import os
import unittest
from shutil import rmtree

from gnes.document import UniSentDocument, MultiSentDocument
from gnes.encoder import PipelineEncoder
from gnes.encoder import GPTEncoder
from gnes.module import GNES


class TestElmoEncoder(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'gpt_encoder.bin')
        self.gpt_path = os.path.join(dirname, 'yaml', 'gpt-binary-encoder.yml')
        self.nes_path = os.path.join(dirname, 'yaml', 'base-gpt-nes.yml')
        self.db_path = './test_leveldb'

        self.test_data1 = UniSentDocument.from_file(
            os.path.join(dirname, 'sonnets.txt'))
        self.test_data2 = MultiSentDocument.from_file(
            os.path.join(dirname, 'sonnets.txt'))
        self.test_str = [s for d in self.test_data1 for s in d.sentences]

    def test_encoding(self):
        _encoder = GPTEncoder(
            model_dir=os.environ.get(
                'GPT_CI_MODEL',
                '/openai_gpt'
            ),
            pooling_strategy="REDUCE_MEAN")
        vec = _encoder.encode(self.test_str)
        self.assertEqual(vec.shape[0], len(self.test_str))
        self.assertEqual(vec.shape[1], 768)

        num_bytes = 8

        gpt = PipelineEncoder.load_yaml(self.gpt_path)
        self.assertRaises(RuntimeError, gpt.encode)

        gpt.train(self.test_str)
        out = gpt.encode(self.test_str)
        gpt.close()
        self.assertEqual(bytes, type(out))
        self.assertEqual(len(self.test_str) * num_bytes, len(out))

        gpt.dump(self.dump_path)
        self.assertTrue(os.path.exists(self.dump_path))
        gpt2 = PipelineEncoder.load(self.dump_path)
        out2 = gpt2.encode(self.test_str)
        self.assertEqual(out, out2)

        nes = GNES.load_yaml(self.nes_path)

        self.assertRaises(RuntimeError, nes.add, self.test_data1)
        self.assertRaises(RuntimeError, nes.query, self.test_data1, 1)

        nes.train(self.test_data1)
        nes.add(self.test_data1)
        query = [s for d in self.test_data1 for s in d.sentences]
        result = nes.query(query, top_k=2)
        self.assertEqual(len(query), len(result))
        self.assertEqual(len(result[0]), 2)
        for q, r in zip(query, result):
            print('q: %s\tr: %s' % (q, r))

        # test dump and loads
        nes.dump(self.dump_path)
        nes.close()
        self.assertTrue(os.path.exists(self.dump_path))
        nes2 = GNES.load(self.dump_path)
        result2 = nes2.query(query, top_k=2)
        self.assertEqual(result, result2)
        nes2.close()

    def tearDown(self):
        if os.path.exists(self.db_path):
            rmtree(self.db_path)

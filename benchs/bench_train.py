import numpy as np
import sys
import os
import json
from memory_profiler import memory_usage
sys.path.append('../')
from src.nes import DummyNES
from src.nes.document import UniSentDocument
os.environ['BERT_CI_PORT'] = '7125'
os.environ['BERT_CI_PORT_OUT'] = '7126'


def get_docs():
    with open('./test/doc.txt', 'r') as f:
        doc = f.readlines()
        doc = [UniSentDocument(d.strip()) for d in doc if d.strip()]
    return doc


doc = get_docs()
queries, labels = get_query()
db_path = './test_leveldb'

nes = DummyNES(pca_output_dim=200,
               num_bytes=20,
               cluster_per_byte=255,
               port=int(os.environ['BERT_CI_PORT']),
               port_out=int(os.environ['BERT_CI_PORT_OUT']),
               data_path=db_path)

nes.train(doc)
nes.add(doc)
nes.close()

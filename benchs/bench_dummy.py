import numpy as np
import sys, os
import json
sys.path.append('../')
from src.nes import DummyNES
from src.nes.document import UniSentDocument
import time
from bert_serving.server.helper import get_args_parser


def get_docs():
    with open('./data/doc.txt', 'r') as f:
        doc = f.readlines()
        doc = [UniSentDocument(d) for d in doc if d.strip()]
    return doc


def get_query():
    queries = []
    labels = []
    with open('./data/label.json.mini', 'r') as f:
        for line in f.readlines():
            if line:
                line = json.loads(line)
                q, rank = line['query'], line['rank']
                queries.append(q)
                labels.append(rank)

    return queries, labels

args = get_args_parser().parse_args(['-model_dir', os.environ['BERT_CI_MODEL'],
                                     '-port', os.environ['BERT_CI_PORT'],
                                     '-port_out', os.environ['BERT_CI_PORT_OUT'],
                                     '-max_seq_len', 'NONE',
                                     '-mask_cls_sep',
                                     '-cpu'])


doc = get_docs()
queries, labels = get_query()
db_path = './test_leveldb'

nes = DummyNES(pca_output_dim=32,
               cluster_per_byte=8,
               port=int(os.environ['BERT_CI_PORT']),
               port_out=int(os.environ['BERT_CI_PORT_OUT']),
               data_path=db_path)
nes.train(doc)
nes.add(doc)
t = nes.query(queries, top_k=10)
for qi, ti in zip(queries, t):
    print(qi)
    for tii in ti:
        print(tii[0]['content'], tii[1])
    print('\n'*3)
nes.close()
server.close()
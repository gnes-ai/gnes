import json
import os
import sys

import numpy as np

sys.path.append('../')
from src.nes import BaseNES
from src.nes.document import UniSentDocument
os.environ['BERT_CI_PORT'] = '7125'
os.environ['BERT_CI_PORT_OUT'] = '7126'


def get_docs():
    with open('./test/doc.txt', 'r') as f:
        doc = f.readlines()
        doc = [UniSentDocument(d.strip()) for d in doc if d.strip()]
    return doc


def get_query():
    queries = []
    labels = []
    with open('./test/label.json.mini', 'r') as f:
        for line in f.readlines():
            if line:
                line = json.loads(line)
                q, rank = line['query'], line['rank']
                queries.append(q)
                labels.append(rank)

    return queries, labels


def extract_content(t):
    pred = []
    for ti in t:
        s = []
        for tii in ti[1:]:
            _doc, _score = tii
            if 'content' in _doc:
                s.append((_doc['content'], _score))
        pred.append(s)
    return pred

# only consider top 10 doc in each label
def NDCG(labels, preds):
    score = []
    W = 0
    for l, p in zip(labels, preds):
        l = sorted(l, key=lambda x: -x[1])
        w = np.log(sum([_[1] for _ in l]))
        s = [_[0] for _ in l]
        p = [_[0] for _ in p]
        bs = [i[1] for i in l[:10]] + [0] * (10 - len(l[:10]))
        rs = [0 if pi not in s else l[s.index(pi)][1] for pi in p]
        print(bs, rs, s, p)
        dcg_max = sum([(2**j)/np.log(i+2) for i, j in enumerate(bs)])
        dcg = sum([(2**j)/np.log(i+2) for i, j in enumerate(rs)])
        score.append(dcg / dcg_max * w)
        W += w
    print(score)
    return np.sum(score)/W


doc = get_docs()
queries, labels = get_query()
db_path = './test_leveldb'

nes = BaseNES(pca_output_dim=400,
              num_bytes=40,
              cluster_per_byte=255,
              port=int(os.environ['BERT_CI_PORT']),
              port_out=int(os.environ['BERT_CI_PORT_OUT']),
              data_path=db_path)
nes.train(doc)
nes.add(doc)

preds = extract_content(nes.query(queries, top_k=11))
nes.close()
with open('preds.json', 'w') as f:
    for q, r in zip(queries, preds):
        f.write(json.dumps({'query': q, 'rank': r}, ensure_ascii=False)+'\n')
print(NDCG(labels, preds))

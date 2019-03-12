import sys
import os
import json
from memory_profiler import memory_usage
sys.path.append('../')
from src.nes import DummyNES
from src.nes.document import UniSentDocument, MultiSentDocument
os.environ['NES_PROFILING'] = '1'
os.environ['BERT_CI_PORT'] = '7125'
os.environ['BERT_CI_PORT_OUT'] = '7126'


def prepare_data(unisent=True):
    docs = []
    for _dir in os.listdir('/ext_data/wiki_zh'):
        for _file in os.listdir(os.path.join('/ext_data/wiki_zh/', _dir)):
            for line in open(_file, 'r').readlines():
                try:
                    line = json.loads(line)
                    if unisent:
                        docs.append(UniSentDocument(line['title'], int(line['id'])))
                    else:
                        docs.append(MultiSentDocument(line['text'], int(line['id'])))
                except Exception:
                    continue
    return docs


def bench_train(docs):
    db_path = './test_leveldb'

    nes = DummyNES(pca_output_dim=200,
                   num_bytes=20,
                   cluster_per_byte=255,
                   port=int(os.environ['BERT_CI_PORT']),
                   port_out=int(os.environ['BERT_CI_PORT_OUT']),
                   data_path=db_path)

    nes.train(docs)
    nes.add(docs)
    nes.close()
    return 


if __name__ == '__main__':
    for unisent in [True, False]:
        docs = prepare_data(unisent)
        bench_train(docs)

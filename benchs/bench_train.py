import sys
import os
import json
from memory_profiler import memory_usage
sys.path.append('../')
from src.nes import DummyNES
from src.nes.document import UniSentDocument, MultiSentDocument
from src.nes.helper import profile_logger
os.environ['NES_PROFILING'] = '1'
os.environ['BERT_CI_PORT'] = '7125'
os.environ['BERT_CI_PORT_OUT'] = '7126'


def prepare_data(unisent=True):
    docs = []
    num_sentences = 0
    for _dir in os.listdir('/ext_data/wiki_zh'):
        _sub_dir = os.listdir(os.path.join('/ext_data/wiki_zh/', _dir))
        for _file in _sub_dir:
            _file_path = os.path.join('/ext_data/wiki_zh/', _dir, _file)
            for line in open(_file_path, 'r').readlines():
                try:
                    line = json.loads(line)
                    if unisent:
                        doc = UniSentDocument(line['title'], int(line['id']))
                    else:
                        doc = MultiSentDocument(line['text'], int(line['id']))
                    num_sentences += len(doc._sentences)
                    docs.append(doc)
                except Exception:
                    continue

    return docs, num_sentences


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
        docs, num_sentences = prepare_data(unisent)
        profile_logger.info('num docs {}, num sentences {}'.format(
                            len(docs), num_sentences))
        bench_train(docs)

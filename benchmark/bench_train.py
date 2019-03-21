import json
import os

from gnes import GNES
from gnes.document import UniSentDocument, MultiSentDocument
from gnes.helper import profile_logger
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
    dump_path = 'test/base-nes.yml'
    nes = GNES.load_yaml(dump_path)

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

import json
import os

from gnes import GNES
from gnes.document import UniSentDocument, MultiSentDocument
os.environ['NES_PROFILING'] = '1'
os.environ['BERT_CI_PORT'] = '7125'
os.environ['BERT_CI_PORT_OUT'] = '7126'


def prepare_data(unisent=True):
    doc_path = '/ext_data/gnes/PKU-Chinese-Paraphrase-Corpus/formated.test.json'
    data = json.loads(open(doc_path, 'r').read())
    all_docs = []
    for line in data.keys() + data.values():
        if unisent:
            all_docs.append(UniSentDocument(line))
        else:
            all_docs.append(MultiSentDocument(line))

    return all_docs, data


def stat(docs, kv_data):
    dump_path = 'test/base-eu-nes.yml'
    nes = GNES.load_yaml(dump_path)

    nes.train(docs)
    nes.add(docs)
    keys = [*kv_data.keys()]
    label = list(kv_data.values())
    res = nes.query(label, 2)
    count = 0
    for l, v in zip(keys, res):
        if res[0][0]['content'] == l:
            count += 1
    print(count / len(label))
    return


if __name__ == '__main__':
    for unisent in [True, False]:
        docs, kv_data = prepare_data(unisent)
        stat(docs, kv_data)

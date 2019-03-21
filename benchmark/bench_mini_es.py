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
    for line in [*data.keys()]:
        if unisent:
            all_docs.append(UniSentDocument(line))
        else:
            all_docs.append(MultiSentDocument(line))

    return all_docs, data


def stat(docs, kv_data):
    dump_path = 'tests/yaml/base-eu-nes.yml'
    dnes = GNES.load_yaml(dump_path)

    dnes.train(docs)
    dnes.add(docs)
    dnes.dump('./t.pkl')
    dnes.close()


    nes = GNES.load('./t.pkl')
    keys = [*kv_data.keys()]
    label = list(kv_data.values())
    res = nes.query(label, 2)
    count = 0
    for j, k, l in zip(label[:20], keys[:20], res[:20]):
        print('Q: {}\n L: {}\nRE: {}\n\n'.format(j, k, l))
    for l, v in zip(keys, res):
        if v[0][0]['content'] == l:
            count += 1
    print(count / len(label))
    return


if __name__ == '__main__':
    for unisent in [True]:
        docs, kv_data = prepare_data(unisent)
        stat(docs, kv_data)

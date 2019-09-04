import os
import re
from typing import TextIO, List

from gnes.proto import gnes_pb2


def txt_file2pb_docs(fp: TextIO, start_id: int = 0) -> List['gnes_pb2.Document']:
    data = [v for v in fp if v.strip()]
    docs = []
    for doc_id, doc_txt in enumerate(data, start_id):
        doc = line2pb_doc(doc_txt, doc_id)
        docs.append(doc)
    return docs


def line2pb_doc(line: str, doc_id: int = 0, deliminator: str = r'[.。！？!?]+') -> 'gnes_pb2.Document':
    doc = gnes_pb2.Document()
    doc.doc_id = doc_id
    doc.doc_type = gnes_pb2.Document.TEXT
    doc.meta_info = line.encode()
    if deliminator:
        for ci, s in enumerate(re.split(deliminator, line)):
            if s.strip():
                c = doc.chunks.add()
                c.doc_id = doc_id
                c.text = s
                c.offset = ci
    else:
        c = doc.chunks.add()
        c.doc_id = doc_id
        c.text = line
        c.offset = 0
    return doc


env_dict = {
    'orange-ci': {
        'BERT_CI_PORT': 7125,
        'BERT_CI_PORT_OUT': 7126,
        'BERT_CI_MODEL': '/chinese_L-12_H-768_A-12',
        'ELMO_CI_MODEL': '/zhs.model',
        'FLAIR_CI_MODEL': '/multi-forward-fast',
        'GPT_CI_MODEL': '/openai_gpt',
        'GPT2_CI_MODEL': '/openai_gpt2',
        'XL_CI_MODEL': '/transformer_xl_wt103',
        'WORD2VEC_MODEL': '/sgns.wiki.bigram-char.sample',
        'VGG_MODEL': '/',
        'RESNET_MODEL': '/',
        'INCEPTION_MODEL': '/',
        'MOBILENET_MODEL': '/',
        'FASTERRCNN_MODEL': '/',
        'GNES_PROFILING': '',
        'TORCH_TRANSFORMERS_MODEL': '/torch_transformer'
        # 'VGGISH_MODEL': '/lab/vggish',
        # 'YT8M_INCEPTION': '/lab/yt8m_incep_v3',
        # 'YT8M_PCA_MODEL': '/lab/yt8m_pca',
        # 'YT8M_MODEL': '/lab/yt8m_model'
    },
    'idc-165': {
        'BERT_CI_PORT': 7125,
        'BERT_CI_PORT_OUT': 7126,
        'BERT_CI_MODEL': '/ext_data/chinese_L-12_H-768_A-12',
        'ELMO_CI_MODEL': '/ext_data/zhs.model',
        'FLAIR_CI_MODEL': '/ext_data/multi-forward-fast',
        'GPT_CI_MODEL': '/ext_data/openai_gpt',
        'GPT2_CI_MODEL': '/ext_data/openai_gpt2',
        'XL_CI_MODEL': '/ext_data/transformer_xl_wt103',
        'WORD2VEC_MODEL': '/ext_data/sgns.wiki.bigram-char.sample',
        'VGG_MODEL': '/ext_data/image_encoder',
        'RESNET_MODEL': '/ext_data/image_encoder',
        'INCEPTION_MODEL': '/ext_data/image_encoder',
        'MOBILENET_MODEL': '/ext_data/image_encoder',
        'FASTERRCNN_MODEL': '/ext_data/image_preprocessor',
        'GNES_PROFILING': '',
        'TORCH_TRANSFORMERS_MODEL': '/ext_data/torch_transformer'
        # 'VGGISH_MODEL': '/ext_data/lab/vggish',
        # 'YT8M_INCEPTION': '/ext_data/lab/yt8m_incep_v3',
        # 'YT8M_PCA_MODEL': '/ext_data/lab/yt8m_pca',
        # 'YT8M_MODEL': '/ext_data/lab/yt8m_model'
    }

}

for k, v in env_dict[os.environ.get('GNES_ENV_SET', 'idc-165')].items():
    if k not in os.environ:
        os.environ[k] = str(v)
    else:
        print('os.environ["%s"]=%s exists already, i wont set it to %s' % (k, os.environ[k], str(v)))

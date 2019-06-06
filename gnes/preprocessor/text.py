import re
from typing import TextIO, List

from ..proto import gnes_pb2

deliminator_cn_en = r'[.。！？!?]+'


def txt_file2pb_docs(fp: TextIO, start_id: int = 0) -> List['gnes_pb2.Document']:
    data = [v for v in fp if v.strip()]
    docs = []
    for doc_id, doc_txt in enumerate(data, start_id):
        doc = line2pb_doc(doc_txt, doc_id)
        docs.append(doc)
    return docs


def line2pb_doc(line: str, doc_id: int = 0) -> 'gnes_pb2.Document':
    doc = gnes_pb2.Document()
    doc.doc_id = doc_id
    doc.doc_type = gnes_pb2.Document.TEXT
    doc.meta_info = line.encode()
    for ci, s in enumerate(re.split(deliminator_cn_en, line)):
        if s.strip():
            c = doc.chunks.add()
            c.doc_id = doc_id
            c.text = s
            c.offset_1d = ci
    return doc

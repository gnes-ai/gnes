import ctypes
import random
import re

from ..base import BasePreprocessor
from ...proto import gnes_pb2


class TextPreprocessor(BasePreprocessor):
    def __init__(self, start_doc_id: int = 0,
                 random_doc_id: bool = True,
                 deliminator: str = r'[.。！？!?]+',
                 do_strip: bool = True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_doc_id = start_doc_id
        self.random_doc_id = random_doc_id
        self.deliminator = deliminator
        self.do_strip = do_strip
        self.is_trained = True

    def apply(self, doc: 'gnes_pb2.Document'):
        doc.doc_id = self.start_doc_id if not self.random_doc_id else random.randint(0, ctypes.c_uint(-1).value)
        doc.doc_type = gnes_pb2.Document.TEXT
        raw_text = doc.raw_text.strip() if self.do_strip else doc.raw_text
        if self.deliminator:
            for ci, s in enumerate(re.split(self.deliminator, raw_text)):
                if s.strip():
                    c = doc.chunks.add()
                    c.doc_id = doc.doc_id
                    c.text = s.strip()
                    c.offset_1d = ci
        else:
            c = doc.chunks.add()
            c.doc_id = doc.doc_id
            c.text = raw_text
            c.offset_1d = 0

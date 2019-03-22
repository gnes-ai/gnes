import ctypes
import random
from typing import Iterator, List

from ..helper import cn_sent_splitter, doc_logger

__all__ = ['BaseDocument', 'UniSentDocument', 'MultiSentDocument']


class BaseDocument:
    def __init__(self, text: str, doc_id: int = None):
        self._id = random.randint(0, ctypes.c_uint(-1).value) if doc_id is None else doc_id
        self._content = text
        self._sentences = self.parse_sentences(text)

    def parse_sentences(self, text: str) -> List[str]:
        raise NotImplementedError

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.__dict__)

    @property
    def id(self) -> int:
        return self._id

    @property
    def sentences(self) -> List[str]:
        return self._sentences

    @classmethod
    def from_file(cls, file_path: str,
                  min_seq_length: int = None,
                  max_seq_length: int = None,
                  max_num_doc: int = None) -> Iterator['BaseDocument']:
        num_doc = 0
        with open(file_path, encoding='utf8') as fp:
            for v in fp:
                if max_num_doc is not None and num_doc >= max_num_doc:
                    break
                v = v.strip()
                if min_seq_length is not None and len(v) < min_seq_length:
                    v = ''
                if max_seq_length is not None:
                    v = v[:max_seq_length]
                if v.strip():
                    doc = cls(v)
                    if check_doc_valid(doc):
                        num_doc += 1
                        yield doc


class UniSentDocument(BaseDocument):
    def parse_sentences(self, text: str):
        return [text]


class MultiSentDocument(BaseDocument):
    def parse_sentences(self, text: str):
        return list(cn_sent_splitter.split(text))


def check_doc_valid(doc: 'BaseDocument') -> bool:
    texts = doc.sentences
    if not isinstance(texts, list):
        doc_logger.error('"%s" must be %s, but received %s' % (texts, type([]), type(texts)))
        return False
    if not len(texts):
        doc_logger.error(
            '"%s" must be a non-empty list, but received %s with %d elements' % (texts, type(texts), len(texts)))
        return False
    for idx, s in enumerate(texts):
        if not isinstance(s, str):
            doc_logger.error('all elements in the list must be %s, but element %d is %s' % (type(''), idx, type(s)))
            return False
        if not s.strip():
            doc_logger.error('all elements in the list must be non-empty string, but element %d is %s' % (idx, repr(s)))
            return False
    return True

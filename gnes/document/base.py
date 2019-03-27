import ctypes
from typing import List

import numpy as np

from ..helper import cn_sent_splitter, doc_logger


class BaseDocument:
    def __init__(self, text: str, doc_id: int = None, **kwargs):
        self.id = np.random.randint(0, ctypes.c_uint(-1).value) if doc_id is None else doc_id
        self.content = text
        self.sentences = filter_sentences(self.parse_sentences(text), **kwargs)
        self.sentence_ids = np.random.randint(0, ctypes.c_uint(-1).value, len(self.sentences),
                                              dtype=np.uint32).tolist()

    def parse_sentences(self, text: str) -> List[str]:
        raise NotImplementedError

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.__dict__)

    @classmethod
    def from_list(cls, c: List[str], max_num_doc: int = None, **kwargs) -> List['BaseDocument']:
        result = []
        for d in c:
            result.append(cls(d, *kwargs))
            if max_num_doc is not None and len(result) >= max_num_doc:
                break
        return result

    @classmethod
    def from_file(cls, file_path: str, **kwargs) -> List['BaseDocument']:
        with open(file_path, encoding='utf8') as fp:
            return cls.from_list([v.strip() for v in fp.readlines()], **kwargs)


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


def filter_sentences(lst: List[str],
                     min_len_seq: int = None,
                     max_len_seq: int = None,
                     max_num_seq: int = None,
                     cutoff: bool = False,
                     strip: bool = True,
                     to_lower: bool = False) -> List[str]:
    result = []
    for s in lst:
        if cutoff and max_len_seq:
            s = s[:max_len_seq]
        if strip:
            s = s.strip()
        if to_lower:
            s = s.lower()
        if min_len_seq and len(s) < min_len_seq:
            s = ''
        if max_len_seq and len(s) > max_len_seq:
            s = ''
        if s:
            result.append(s)
            if max_num_seq and len(result) >= max_num_seq:
                break
    return result

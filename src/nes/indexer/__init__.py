from typing import List, Tuple, Any
import json
from ..document import BaseDocument
from ..helper import set_logger
from .leveldb import BaseLVDB


class BaseIndexer:
    def __init__(self, *args, **kwargs):
        self.logger = set_logger(self.__class__.__name__, 'verbose' in kwargs and kwargs['verbose'])

    def add(self, *args, **kwargs): pass

    def query(self, *args, **kwargs) -> List[List[Tuple[Any, float]]]: pass

    def dump(self, *args, **kwargs): pass

    def load(self, *args, **kwargs): pass


class BaseBinaryIndexer(BaseIndexer):
    def __init__(self):
        super().__init__()

    def add(self, vectors: bytes, doc_ids: bytes):
        pass

    def query(self, keys: bytes, top_k: int) -> List[List[Tuple[int, float]]]:
        pass


class BaseTextIndexer(BaseIndexer):
    def __init__(self, data_path: str):
        super().__init__()
        self.basedb = BaseLVDB(data_path)

    def add(self, docs: List[BaseDocument]):
        doc_ids = [bytes(str(doc._id), 'utf8') for doc in docs]
        contents = [self.doc2bytes(doc) for doc in docs]
        self.basedb.add(doc_ids, contents)

    def query(self, keys: List[int]) -> List[dict]:
        doc_ids = [bytes(str(key), 'utf8') for key in keys]
        contents = self.basedb.query(doc_ids)
        return [self.bytes2doc(content) for content in contents]

    def doc2bytes(self, doc: BaseDocument):
        # doc._sentences is iterator, which can't be dumped.
        return bytes(json.dumps({
                            'id': doc._id,
                            'sentences': list(doc._sentences),
                            'content': doc._content},
                           ensure_ascii=False), 'utf8')

    def bytes2doc(self, content):
        if content:
            return json.loads(content.decode())
        else:
            return {}

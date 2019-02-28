import plyvel
from typing import List


class BaseLVDB:
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.db = plyvel.DB(self.data_path, create_if_missing=True)
        self.miss_token = None

    def add(self, doc_ids: List[bytes], contents: List[bytes]):
        if len(doc_ids) != len(contents):
            raise ValueError('doc_ids and contents should be same length!')

        with self.db.write_batch() as wb:
            for doc_id, line in zip(doc_ids, contents):
                wb.put(doc_id, line)

        return 'suc'

    def query(self, doc_ids: List[bytes]):
        res = []
        for doc_id in doc_ids:
            v = self.db.get(doc_id)
            if v:
                res.append(v)
            else:
                res.append(self.miss_token)
        return res

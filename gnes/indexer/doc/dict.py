from typing import List

from google.protobuf.json_format import MessageToJson, Parse

from ..base import BaseDocIndexer
from ...proto import gnes_pb2


class DictIndexer(BaseDocIndexer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._content = {}

    def add(self, keys: List[int], docs: List['gnes_pb2.Document'], *args, **kwargs):
        self._content.update({k: MessageToJson(d) for (k, d) in zip(keys, docs)})

    def query(self, keys: List[int], *args, **kwargs) -> List['gnes_pb2.Document']:
        return [Parse(self._content[k], gnes_pb2.Document()) for k in keys]

    @property
    def size(self):
        return len(self._content)

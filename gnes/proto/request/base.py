from typing import List, Any, Generator

from .. import gnes_pb2


class BaseRequestGenerator:
    def index(self, docs: List[Any], *args, **kwargs) -> Generator['gnes_pb2.Request', None, None]:
        raise NotImplementedError

    def query(self, query: Any, top_k: int, *args, **kwargs) -> Generator['gnes_pb2.Request', None, None]:
        raise NotImplementedError

    def train(self, docs: List[Any], batch_size: int, *args, **kwargs) -> Generator['gnes_pb2.Request', None, None]:
        raise NotImplementedError

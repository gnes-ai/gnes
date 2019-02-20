import ctypes
import random
from typing import Iterator

from src.nes.helper import cn_sent_splitter


class BaseDocument:
    def __init__(self):
        self._id = random.randint(0, ctypes.c_uint(-1).value)
        self._sentences = []

    @property
    def id(self) -> int:
        return self._id

    @property
    def sentences(self) -> Iterator[str]:
        return self._sentences


class UniSentDocument(BaseDocument):
    def __init__(self, text):
        super().__init__()
        self._sentences = [text]


class MultiSentDocument(BaseDocument):
    def __init__(self, text):
        super().__init__()
        self._sentences = cn_sent_splitter.split(text)

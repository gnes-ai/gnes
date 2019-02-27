from functools import wraps
from typing import List

from bert_serving.client import BertClient


class BaseEncoder:
    def __init__(self, *args, model_path=None, **kwargs):
        self.model_path = model_path
        self.is_trained = False

    def encode(self, *args, **kwargs):
        pass

    def train(self, *args, **kwargs):
        pass

    def save(self, *args, **kwargs):
        pass

    def train_required(func):
        @wraps(func)
        def arg_wrapper(self, *args, **kwargs):
            if self.is_trained:
                return func(self, *args, **kwargs)
            else:
                raise RuntimeError('pretraining is required for this function')

        return arg_wrapper

    def as_train_func(func):
        @wraps(func)
        def arg_wrapper(self, *args, **kwargs):
            f = func(self, *args, **kwargs)
            self.is_trained = True
            return f

        return arg_wrapper


class BaseBinaryEncoder(BaseEncoder):
    def encode(self, texts: List[str]) -> bytes: pass


class BertEncoder(BaseEncoder, BertClient):
    def __init__(self, *args, **kwargs):
        BertClient.__init__(*args, **kwargs)

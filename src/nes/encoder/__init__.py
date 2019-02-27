from functools import wraps
from typing import List

from bert_serving.client import BertClient

from ..helper import set_logger


class BaseEncoder:
    def __init__(self, *args, **kwargs):
        self.is_trained = False
        self.logger = set_logger(self.__class__.__name__, 'verbose' in kwargs and kwargs['verbose'])

    def encode(self, *args, **kwargs):
        pass

    def train(self, *args, **kwargs):
        pass

    def dump(self, *args, **kwargs):
        pass

    def load(self, *args, **kwargs):
        pass

    def train_required(func):
        @wraps(func)
        def arg_wrapper(self, *args, **kwargs):
            if self.is_trained:
                return func(self, *args, **kwargs)
            else:
                raise RuntimeError('training is required before calling "%s"' % func.__name__)

        return arg_wrapper

    def as_train_func(func):
        @wraps(func)
        def arg_wrapper(self, *args, **kwargs):
            if self.is_trained:
                self.logger.warning('"%s" has been trained already, '
                                    'training it again will override the previous training' % self.__class__.__name__)
            f = func(self, *args, **kwargs)
            self.is_trained = True
            return f

        return arg_wrapper


class BaseBinaryEncoder(BaseEncoder):
    def encode(self, texts: List[str]) -> bytes: pass


class BertEncoder(BaseEncoder, BertClient):
    def __init__(self, *args, **kwargs):
        BertClient.__init__(*args, **kwargs)

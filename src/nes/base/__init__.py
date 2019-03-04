import pickle
from functools import wraps

from ..helper import set_logger, time_profile


class TrainableBase:
    _timeit = time_profile

    def __init__(self, *args, **kwargs):
        # common
        self.is_trained = False
        self.verbose = 'verbose' in kwargs and kwargs['verbose']
        self.logger = set_logger(self.__class__.__name__, self.verbose)

    def __getstate__(self):
        d = dict(self.__dict__)
        del d['logger']
        return d

    def __setstate__(self, d):
        self.__dict__.update(d)
        self.logger = set_logger(self.__class__.__name__, self.verbose)

    @staticmethod
    def _train_required(func):
        @wraps(func)
        def arg_wrapper(self, *args, **kwargs):
            if self.is_trained:
                return func(self, *args, **kwargs)
            else:
                raise RuntimeError('training is required before calling "%s"' % func.__name__)

        return arg_wrapper

    @staticmethod
    def _as_train_func(func):
        @wraps(func)
        def arg_wrapper(self, *args, **kwargs):
            if self.is_trained:
                self.logger.warning('"%s" has been trained already, '
                                    'training it again will override the previous training' % self.__class__.__name__)
            f = func(self, *args, **kwargs)
            self.is_trained = True
            return f

        return arg_wrapper

    @_timeit
    def dump(self, filename: str):
        with open(filename, 'wb') as fp:
            pickle.dump(self, fp)

    @staticmethod
    @_timeit
    def load(filename: str) -> 'TrainableBase':
        with open(filename, 'rb') as fp:
            return pickle.load(fp)

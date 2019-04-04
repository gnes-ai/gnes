import torch
import torch.nn as nn

from ...helper import set_logger


class BaseTorchModel(nn.Module):

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.use_cuda = kwargs.get('use_cuda', torch.cuda.is_available())
        self.batch_size = kwargs.get('batch_size', 250)
        self.verbose = 'verbose' in kwargs and kwargs['verbose']
        self.logger = set_logger(self.__class__.__name__, self.verbose)
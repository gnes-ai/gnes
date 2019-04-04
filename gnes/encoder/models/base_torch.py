import torch
import torch.nn as nn

from ...helper import set_logger


class BaseTorchModel(nn.Module):

    def __init__(self, model_dir, use_cuda=None, *args, **kwargs):
        super().__init__()
        self.model_dir = model_dir
        self.verbose = 'verbose' in kwargs and kwargs['verbose']
        self.logger = set_logger(self.__class__.__name__, self.verbose)
        self.use_cuda = use_cuda if use_cuda is not None else torch.cuda.is_available(
        )

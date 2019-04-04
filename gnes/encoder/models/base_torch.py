import torch
import torch.nn as nn

from . import BaseModel


class BaseTorchModel(BaseModel, nn.Module):
    def __init__(self, model_dir, use_cuda=None, *args, **kwargs):
        super().__init__(model_dir, *args, **kwargs)
        self.use_cuda = use_cuda if use_cuda is not None else torch.cuda.is_available()

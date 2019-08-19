from typing import List

import numpy as np

from gnes.encoder.base import BaseTextEncoder


class PyTorchTransformers(BaseTextEncoder):

    def __init__(self, model_name: str = 'bert-base-uncased', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_name = model_name

    def encode(self, text: List[str], *args, **kwargs):
        return np.random.random([5, 128])

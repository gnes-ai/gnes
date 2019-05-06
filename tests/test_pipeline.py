import os
from typing import Any

import numpy as np

from gnes.encoder.base import PipelineEncoder, BinaryEncoder, BaseEncoder
from gnes.helper import TimeContext

os.environ['NES_PROFILING'] = ''


class IdentityEncoder(BaseEncoder):
    def encode(self, data: Any, *args, **kwargs):
        return data


class dummyPipeline(PipelineEncoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.component = lambda: [IdentityEncoder(),
                                  BinaryEncoder(),
                                  IdentityEncoder(),
                                  IdentityEncoder(),
                                  IdentityEncoder(),
                                  IdentityEncoder(),
                                  IdentityEncoder(),
                                  IdentityEncoder(),
                                  IdentityEncoder(),
                                  IdentityEncoder(), ]


with TimeContext('pipline'):
    a = np.random.randint(0, 255, [10, 20], dtype='uint8')
    p = dummyPipeline()
    p.encode(a)

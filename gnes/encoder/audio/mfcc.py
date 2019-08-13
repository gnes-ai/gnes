#  Tencent is pleased to support the open source community by making GNES available.
#
#  Copyright (C) 2019 THL A29 Limited, a Tencent company. All rights reserved.
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.


from typing import List

import numpy as np

from ..base import BaseAudioEncoder
from ...helper import batching


class MfccEncoder(BaseAudioEncoder):
    batch_size = 64

    def __init__(self, n_mfcc: int = 13, sample_rate: int = 16000, max_length: int = 100, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.n_mfcc = n_mfcc
        self.sample_rate = sample_rate
        self.max_length = max_length

    @batching
    def encode(self, data: List['np.array'], *args, **kwargs) -> np.ndarray:
        import librosa

        mfccs = [np.array(librosa.feature.mfcc(y=audio, sr=self.sample_rate, n_mfcc=self.n_mfcc).T)
                 for audio in data]

        mfccs = [np.concatenate((mf, np.zeros((self.max_length - mf.shape[0], self.n_mfcc), dtype=np.float32)), axis=0)
                 if mf.shape[0] < self.max_length else mf[:self.max_length] for mf in mfccs]
        mfccs = [mfcc.reshape((1, -1)) for mfcc in mfccs]
        mfccs = np.squeeze(np.array(mfccs), axis=1)
        return mfccs

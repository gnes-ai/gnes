#  Tencent is pleased to support the open source community by making GNES available.
#
#  Copyright (C) 2019 THL A29 Limited, a Tencent company. All rights reserved.
#  Licensed under the Apache License, Version 2.0 (the 'License');
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an 'AS IS' BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import io
import ffmpeg
import numpy as np
import soundfile as sf


def capture_audio(filename: str = 'pipe:',
                  video_data: bytes = None,
                  bits_per_raw_sample: int = 16,
                  sample_rate: int = 16000,
                  **kwargs) -> List['np.ndarray']:

    stream = ffmpeg.input(filename)
    stream = stream.output(
        'pipe:',
        format='wav',
        bits_per_raw_sample=bits_per_raw_sample,
        ac=1,
        ar=16000)

    stdout, err = stream.run(
        input=video_data, capture_stdout=True, capture_stderr=True)

    audio_stream = io.BytesIO(stdout)
    audio_data, sample_rate = sf.read(audio_stream)
    # has multiple channels, do average
    if len(audio_data.shape) == 2:
        audio_data = np.mean(audio_data, axis=1)

    return audio_data

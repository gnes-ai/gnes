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
import re
import ffmpeg
import numpy as np
import soundfile as sf

from typing import List

DEFAULT_SILENCE_DURATION = 0.3
DEFAULT_SILENCE_THRESHOLD = -60


def capture_audio(filename: str = 'pipe:',
                  video_data: bytes = None,
                  bits_per_raw_sample: int = 16,
                  sample_rate: int = 16000,
                  **kwargs) -> List['np.ndarray']:

    capture_stdin = (filename == 'pipe:')
    if capture_stdin and video_data is None:
        raise ValueError(
            "the buffered video data for stdin should not be empty")

    stream = ffmpeg.input(filename)
    stream = stream.output(
        'pipe:',
        format='wav',
        bits_per_raw_sample=bits_per_raw_sample,
        ac=1,
        ar=16000)

    stdout, _ = stream.run(
        input=video_data, capture_stdout=True, capture_stderr=True)

    audio_stream = io.BytesIO(stdout)
    audio_data, sample_rate = sf.read(audio_stream)
    # has multiple channels, do average
    if len(audio_data.shape) == 2:
        audio_data = np.mean(audio_data, axis=1)

    return audio_data


def get_chunk_times(filename: str = 'pipe:',
                    video_data: bytes = None,
                    silence_threshold: float = DEFAULT_SILENCE_THRESHOLD,
                    silence_duration: float = DEFAULT_SILENCE_DURATION,
                    start_time: float = None,
                    end_time: float = None):

    silence_start_re = re.compile(
        ' silence_start: (?P<start>[0-9]+(\.?[0-9]*))$')
    silence_end_re = re.compile(' silence_end: (?P<end>[0-9]+(\.?[0-9]*)) ')
    total_duration_re = re.compile(
        'size=[^ ]+ time=(?P<hours>[0-9]{2}):(?P<minutes>[0-9]{2}):(?P<seconds>[0-9\.]{5}) bitrate='
    )

    input_kwargs = {}
    if start_time is not None:
        input_kwargs['ss'] = start_time
    else:
        start_time = 0.
    if end_time is not None:
        input_kwargs['t'] = end_time - start_time

    stream = ffmpeg.input(filename, **input_kwargs)
    stream = stream.filter(
        'silencedetect',
        n='{}dB'.format(silence_threshold),
        d=silence_duration)
    stream = stream.output('pipe:', format='null')

    stdout, stderr = stream.run(
        input=video_data, capture_stdout=True, capture_stderr=True)

    lines = stderr.decode().splitlines()

    # Chunks start when silence ends, and chunks end when silence starts.
    chunk_starts = []
    chunk_ends = []
    for line in lines:
        silence_start_match = silence_start_re.search(line)
        silence_end_match = silence_end_re.search(line)
        total_duration_match = total_duration_re.search(line)
        if silence_start_match:
            chunk_ends.append(float(silence_start_match.group('start')))
            if len(chunk_starts) == 0:
                # Started with non-silence.
                chunk_starts.append(start_time)
        elif silence_end_match:
            chunk_starts.append(float(silence_end_match.group('end')))
        elif total_duration_match:
            hours = int(total_duration_match.group('hours'))
            minutes = int(total_duration_match.group('minutes'))
            seconds = float(total_duration_match.group('seconds'))
            end_time = hours * 3600 + minutes * 60 + seconds

    if len(chunk_starts) == 0:
        # No silence found.
        chunk_starts.append(start_time)

    if len(chunk_starts) > len(chunk_ends):
        # Finished with non-silence.
        chunk_ends.append(end_time or 10000000.)

    return list(zip(chunk_starts, chunk_ends))


def split_audio(filename: str = 'pipe:',
                video_data: bytes = None,
                silence_threshold=DEFAULT_SILENCE_THRESHOLD,
                silence_duration=DEFAULT_SILENCE_DURATION,
                start_time: float = None,
                end_time: float = None,
                verbose=False):
    chunk_times = get_chunk_times(
        filename,
        video_data=video_data,
        silence_threshold=silence_threshold,
        silence_duration=silence_duration,
        start_time=start_time,
        end_time=end_time)

    audio_chunks = list()
    for i, (start_time, end_time) in enumerate(chunk_times):
        time = end_time - start_time
        stream = ffmpeg.input(filename, ss=start_time, t=time)
        stream = stream.output('pipe:', format='wav')
        stdout, _ = stream.run(
            input=video_data, capture_stdout=True, capture_stderr=True)

        audio_stream = io.BytesIO(stdout)
        audio_data, sample_rate = sf.read(audio_stream)
        # has multiple channels, do average
        if len(audio_data.shape) == 2:
            audio_data = np.mean(audio_data, axis=1)
        audio_chunks.append(audio_data)
    return audio_chunks

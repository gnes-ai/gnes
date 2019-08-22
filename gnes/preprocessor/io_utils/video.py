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

import re
import ffmpeg
import numpy as np

from typing import List

from .helper import extract_frame_size


def capture_frames(filename: str = 'pipe:',
                   video_data: bytes = None,
                   pix_fmt: str = 'rgb24',
                   fps: int = -1,
                   scale: str = None,
                   **kwargs) -> List['np.ndarray']:
    capture_stdin = (filename == 'pipe:')
    if capture_stdin and video_data is None:
        raise ValueError(
            "the video data buffered from stdin should not be empty")

    # discard corrupted frames
    # https://stackoverflow.com/questions/45983605/ffmpeg-jpg-frame-capture-how-to-discard-corrupted-frames
    stream = ffmpeg.input(filename, err_detect="aggressive", fflags="discardcorrupt")
    if fps > 0:
        stream = stream.filter('fps', fps=fps, round='up')

    if scale:
        width, height = scale.split(':')
        stream = stream.filter('scale', width, height)

    stream = stream.output('pipe:', format='rawvideo', pix_fmt=pix_fmt)

    out, err = stream.run(
        input=video_data, capture_stdout=True, capture_stderr=True)

    width, height = extract_frame_size(err.decode())

    depth = 3
    if pix_fmt == 'rgba':
        depth = 4

    frames = np.frombuffer(out, np.uint8).reshape([-1, height, width, depth])
    return list(frames)

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

from typing import List
import numpy as np
import subprocess as sp
import tempfile

from .ffmpeg import compile_args, extract_frame_size
from .helper import _check_input, run_command


def capture_frames(input_fn: str = 'pipe:',
                   input_data: bytes = None,
                   fps: int = None,
                   pix_fmt: str = 'rgb24',
                   vframes: int = -1) -> 'np.ndarray':
    _check_input(input_fn, input_data)



    with tempfile.NamedTemporaryFile(suffix=".gif") as f:
        if input_data:
            f.write(input_data)
            f.flush()
            input_fn = f.name

        video_filters = []
        if fps:
            video_filters += ['fps=%d' % fps]

        output_kwargs = {'format': 'rawvideo', 'pix_fmt': pix_fmt}
        if vframes > 0:
            output_kwargs['vframes'] = vframes

        cmd_args = compile_args(
            input_fn=input_fn,
            video_filters=video_filters,
            output_options=output_kwargs)

        out, err = run_command(cmd_args, pipe_stdout=True, pipe_stderr=True)

        width, height = extract_frame_size(err.decode())

        depth = 3
        if pix_fmt == 'rgba':
            depth = 4

        frames = np.frombuffer(out,
                               np.uint8).reshape([-1, height, width, depth])
        return frames


def encode_video(images: 'np.ndarray', frame_rate: int, pix_fmt: str = 'rgb24'):

    cmd = [
        'ffmpeg', '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo', '-r',
        '%.02f' % frame_rate, '-s',
        '%dx%d' % (images[0].shape[1], images[0].shape[0]), '-pix_fmt',
        'rgb24', '-i', '-', '-filter_complex',
        '[0:v]split[x][z];[z]palettegen[y];[x]fifo[x];[x][y]paletteuse', '-r',
        '%.02f' % frame_rate, '-f', 'gif', '-'
    ]
    proc = sp.Popen(cmd, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
    for image in images:
        proc.stdin.write(image.tostring())
    out, err = proc.communicate()
    if proc.returncode:
        err = '\n'.join([' '.join(cmd), err.decode('utf8')])
        raise IOError(err)
    del proc
    return out

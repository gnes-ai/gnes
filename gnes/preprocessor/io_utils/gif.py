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

from .ffmpeg import parse_media_details



def decode_gif(data: bytes, fps: int = -1,
               pix_fmt: str = 'rgb24') -> 'np.ndarray':
    with tempfile.NamedTemporaryFile(suffix=".gif") as f:
        f.write(data)
        f.flush()

        stream = ffmpeg.input(f.name)
        if fps > 0:
            stream = stream.filter('fps', fps=20, round='up')

        stream = stream.output('pipe:', format='rawvideo', pix_fmt=pix_fmt)

        out, err = stream.run(capture_stdout=True, capture_stderr=True)

        meta_info = parse_media_details(err.decode())
        width = meta_info['frame_width']
        height = meta_info['frame_height']

        depth = 3
        if pix_fmt == 'rgba':
            depth = 4

        frames = np.frombuffer(out,
                               np.uint8).reshape([-1, height, width, depth])
        return frames


def encode_gif(
        images: List[np.ndarray],
        fps: int,
        pix_fmt: str = 'rgb24'):

    cmd = [
        'ffmpeg', '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo', '-r',
        '%.02f' % fps, '-s',
        '%dx%d' % (images[0].shape[1], images[0].shape[0]), '-pix_fmt',
        'rgb24', '-i', '-', '-filter_complex',
        '[0:v]split[x][z];[z]palettegen[y];[x]fifo[x];[x][y]paletteuse', '-r',
        '%.02f' % fps, '-f', 'gif', '-'
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

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
from scipy import ndimage


def decode_gif(data: bytes) -> 'np.ndarray':
    with tempfile.NamedTemporaryFile(suffix=".gif") as f:
        f.write(data)
        f.flush()
        im_array = ndimage.imread(f.name)
        return im_array


def encode_gif(images: List[np.ndarray],
               scale: str,
               # width: int,
               # height: int,
               fps: int,
               pix_fmt: str = 'rgb24'):
    """
    https://superuser.com/questions/556029/how-do-i-convert-a-video-to-gif-using-ffmpeg-with-reasonable-quality
    https://gist.github.com/alexlee-gk/38916bf524dc75ca1b988d113aa30710
    """

    cmd = [
        'ffmpeg', '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo',
        '-r', '%.02f' % fps,
        '-s', '%dx%d' % (images[0].shape[1], images[0].shape[0]),
        '-pix_fmt', 'rgb24',
        '-i', '-',
        '-filter_complex', '[0:v]split[x][z];[z]palettegen[y];[x]fifo[x];[x][y]paletteuse',
        '-r', '%.02f' % fps,
        '-s', scale,
        '-f', 'gif',
        '-']
    proc = sp.Popen(cmd, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
    for frame in frames:
        proc.stdin.write(frame.tostring())
    out, err = proc.communicate()
    if proc.returncode:
        err = '\n'.join([' '.join(cmd), err.decode('utf8')])
        raise IOError(err)
    del proc
    return out

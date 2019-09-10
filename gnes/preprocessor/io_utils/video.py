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
import numpy as np

from typing import List

from .ffmpeg import compile_args, probe
from .helper import _check_input, run_command, run_command_async


def scale_video(input_fn: str = 'pipe:',
                output_fn: str = 'pipe:',
                input_data: bytes = None,
                start_time: float = None,
                end_time: float = None,
                scale: str = None,
                frame_rate: int = 15,
                crf: int = 16,
                vcodec: str = 'libx264',
                format: str = 'mp4',
                pix_fmt: str = 'yuv420p',
                **kwargs):

    _check_input(input_fn, input_data)

    capture_stdout = (output_fn == 'pipe:')

    input_kwargs = {}
    if start_time is not None:
        input_kwargs['ss'] = start_time
    else:
        start_time = 0.
    if end_time is not None:
        input_kwargs['t'] = end_time - start_time

    out_kwargs = {
        'vcodec': vcodec,
        'pix_fmt': pix_fmt,
        'crf': crf,
        'framerate': frame_rate,
        'acodec': 'aac',
        'strict': 'experimental',    # AAC audio encoder is experimental
    }

    if scale:
        out_kwargs['s'] = scale

    if capture_stdout:
        out_kwargs['format'] = format
        # an empty moov means it doesn't need to seek and thus works with a pipe.
        out_kwargs['movflags'] = 'frag_keyframe+empty_moov'

    cmd_args = compile_args(
        input_fn=input_fn,
        output_fn=output_fn,
        input_options=input_kwargs,
        output_options=out_kwargs,
        overwrite_output=True)
    stdout, _ = run_command(
        cmd_args, input=input_data, pipe_stdout=True, pipe_stderr=True)

    if capture_stdout:
        return stdout
    return None


def encode_video(images: 'np.ndarray',
                 pix_fmt: str = 'rgb24',
                 frame_rate: int = 15,
                 output_fn: str = 'pipe:',
                 vcodec: str = 'libx264',
                 format: str = 'mp4',
                 **kwargs):
    packet_size = 4096

    n = len(images)
    height, width, channels = images[0].shape

    capture_stdout = (output_fn == 'pipe:')

    input_kwargs = {
        'format': 'rawvideo',
        'pix_fmt': pix_fmt,
        'framerate': frame_rate,
        's': '{}x{}'.format(width, height),
    }

    output_kwargs = {
        'vcodec': vcodec,
        'r': frame_rate,
        'pix_fmt': 'yuv420p',
        'format': format,
        'movflags': 'frag_keyframe+empty_moov',
    }

    cmd_args = compile_args(
        input_fn='pipe:',
        output_fn=output_fn,
        input_options=input_kwargs,
        output_options=output_kwargs)

    with run_command_async(
            cmd_args,
            pipe_stdin=True,
            pipe_stdout=capture_stdout,
            pipe_stderr=True) as proc:

        input_stream = io.BytesIO(b'')
        for frame in images:
            input_stream.write(frame.astype(np.uint8).tobytes())

        output, err = proc.communicate(input_stream.getvalue())

        if proc.returncode:
            err = '\n'.join([' '.join(cmd_args), err.decode('utf8')])
            raise IOError(err)

        return output


def capture_frames(input_fn: str = 'pipe:',
                   input_data: bytes = None,
                   pix_fmt: str = 'rgb24',
                   fps: int = -1,
                   scale: str = None,
                   start_time: float = None,
                   end_time: float = None,
                   vframes: int = -1,
                   **kwargs) -> List['np.ndarray']:
    _check_input(input_fn, input_data)

    import tempfile

    with tempfile.NamedTemporaryFile() as f:
        if input_data:
            f.write(input_data)
            f.flush()
            input_fn = f.name

        video_meta = probe(input_fn)
        width = video_meta['width']
        height = video_meta['height']

        if scale is not None:
            _width, _height = map(int, scale.split(':'))
            if _width * _height < 0:
                if _width > 0:
                    ratio = _width / width
                    height = int(ratio * height)
                    if _height == -2:
                        height += height % 2
                    width = _width
                else:
                    ratio = _height / height
                    width = int(ratio * width)
                    if _width == -2:
                        width += width % 2

                    height = _height

                scale = '%d:%d' % (width, height)
            else:
                width = _width
                height = _height

        input_kwargs = {
            'err_detect': 'aggressive',
            'fflags': 'discardcorrupt'    # discard corrupted frames
        }
        if start_time is not None:
            input_kwargs['ss'] = str(start_time)
        else:
            start_time = 0.
        if end_time is not None:
            input_kwargs['t'] = str(end_time - start_time)

        video_filters = []
        if fps:
            video_filters += ['fps=%d' % fps]
        if scale:
            video_filters += ['scale=%s' % scale]

        output_kwargs = {
            'format': 'image2pipe',
            'pix_fmt': pix_fmt,
            'vcodec': 'rawvideo',
            'movflags': 'faststart',
        }
        if vframes > 0:
            output_kwargs['vframes'] = vframes

        cmd_args = compile_args(
            input_fn=input_fn,
            input_options=input_kwargs,
            video_filters=video_filters,
            output_options=output_kwargs)
        out, _ = run_command(cmd_args, pipe_stdout=True, pipe_stderr=True)

        depth = 3
        if pix_fmt == 'rgba':
            depth = 4

        frames = np.frombuffer(out,
                               np.uint8).reshape([-1, height, width, depth])
        return frames


# def read_frame_as_jpg(in_filename, frame_num):
#     out, err = (
#         ffmpeg
#         .input(in_filename)
#         .filter_('select', 'gte(n,{})'.format(frame_num))
#         .output('pipe:', vframes=1, format='image2', vcodec='mjpeg')
#         .run(capture_stdout=True)
#     )
#     return out

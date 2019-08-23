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

import ffmpeg
import numpy as np

from typing import List

from .helper import extract_frame_size


def scale_video(input_filename: str = 'pipe:',
                output_filename: str = 'pipe:',
                video_data: bytes = None,
                start_time: float = None,
                end_time: float = None,
                scale: str = None,
                frame_rate: int = 15,
                crf: int = 16,
                vcodec: str = 'libx264',
                format: str = 'mpeg',
                pix_fmt: str = 'yuv420p',
                **kwargs):
    capture_stdin = (input_filename == 'pipe:')
    if capture_stdin and video_data is None:
        raise ValueError(
            "the buffered video data for stdin should not be empty")

    capture_stdout = (output_filename == 'pipe:')

    input_kwargs = {}
    if start_time is not None:
        input_kwargs['ss'] = start_time
    else:
        start_time = 0.
    if end_time is not None:
        input_kwargs['t'] = end_time - start_time

    stream = ffmpeg.input(input_filename, **input_kwargs)

    out_kwargs = {
        'vcodec': vcodec,
        'pix_fmt': pix_fmt,
        'crf': crf,
        's': scale,
        'framerate': frame_rate
    }

    if capture_stdout:
        out_kwargs['format'] = format

    stream = stream.output(output_filename, **out_kwargs).overwrite_output()
    stdout, stderr = stream.run(
        input=video_data if capture_stdin else None,
        capture_stdout=capture_stdout)
    if capture_stdout:
        return stdout
    return None


def encode_video(filename: str,
                 images: List['np.ndarray'],
                 frame_rate: int = 15,
                 vcodec: str = 'libx264',
                 **kwargs):
    packet_size = 4096

    n = len(images)
    height, width, channels = images[0].shape

    capture_stdout = (filename == 'pipe:')
    process = ffmpeg.input(
        'pipe:',
        format='rawvideo',
        pix_fmt='rgb24',
        s='{}x{}'.format(width, height)).output(
            filename, pix_fmt='yuv420p', vcodec=vcodec,
            r=frame_rate).overwrite_output().run_async(
                pipe_stdin=True, pipe_stdout=capture_stdout)
    for frame in images:
        process.stdin.write(frame.astype(np.uint8).tobytes())
    process.stdin.close()

    output = None
    if capture_stdout:
        stream = io.BytesIO(b'')
        while True:
            in_bytes = process.stdout.read(packet_size)
            if not in_bytes:
                process.stdout.close()

                break
            stream.write(in_bytes)

        output = stream.getvalue()
    process.wait()
    return output


def capture_frames(filename: str = 'pipe:',
                   video_data: bytes = None,
                   pix_fmt: str = 'rgb24',
                   fps: int = -1,
                   scale: str = None,
                   start_time: float = None,
                   end_time: float = None,
                   **kwargs) -> List['np.ndarray']:
    capture_stdin = (filename == 'pipe:')
    if capture_stdin and video_data is None:
        raise ValueError(
            "the buffered video data for stdin should not be empty")

    input_kwargs = {
        'err_detect': 'aggressive',
        'fflags': 'discardcorrupt'    # discard corrupted frames
    }
    if start_time is not None:
        input_kwargs['ss'] = start_time
    else:
        start_time = 0.
    if end_time is not None:
        input_kwargs['t'] = end_time - start_time

    stream = ffmpeg.input(filename, **input_kwargs)
    if fps > 0:
        stream = stream.filter('fps', fps=fps, round='up')

    if scale:
        width, height = map(int, scale.split(':'))
        stream = stream.filter('scale', width, height)

    stream = stream.output('pipe:', format='rawvideo', pix_fmt=pix_fmt)

    out, err = stream.run(
        input=video_data, capture_stdout=True, capture_stderr=True)

    if not scale:
        width, height = extract_frame_size(err.decode())

    depth = 3
    if pix_fmt == 'rgba':
        depth = 4

    frames = np.frombuffer(out, np.uint8).reshape(
        [-1, int(height), int(width), depth])
    return list(frames)

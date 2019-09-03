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
from .helper import _check_input, kwargs_to_cmd_args, run_command

VIDEO_DUR_PATTERN = re.compile(r".*Duration: (\d+):(\d+):(\d+)", re.DOTALL)
VIDEO_INFO_PATTERN = re.compile(
    r'.*Stream #0:(\d+)(?:\(\w+\))?: Video: (\w+).*, (\w+)[(,].* (\d+)x(\d+).* (\d+)(\.\d.)? fps',
    re.DOTALL)
AUDIO_INFO_PATTERN = re.compile(
    r'^\s+Stream #0:(?P<stream>\d+)(\((?P<lang>\w+)\))?: Audio: (?P<format>\w+).*?(?P<default>\(default\))?$',
    re.MULTILINE)
STREAM_SUBTITLE_PATTERN = re.compile(
    r'^\s+Stream #0:(?P<stream>\d+)(\((?P<lang>\w+)\))?: Subtitle:',
    re.MULTILINE)


def parse_media_details(infos):
    video_dur_match = VIDEO_DUR_PATTERN.match(infos)
    dur_hrs, dur_mins, dur_secs = video_dur_match.group(1, 2, 3)

    video_info_match = VIDEO_INFO_PATTERN.match(infos)
    codec, pix_fmt, res_width, res_height, fps = video_info_match.group(
        2, 3, 4, 5, 6)

    audio_tracks = list()
    for audio_match in AUDIO_INFO_PATTERN.finditer(infos):
        ainfo = audio_match.groupdict()
        if ainfo['lang'] is None:
            ainfo['lang'] = 'und'
        audio_tracks.append(ainfo)

    medio_info = {
        'vcodec': codec,
        'frame_width': int(res_width),
        'frame_height': int(res_height),
        'duration': (int(dur_hrs) * 3600 + int(dur_mins) * 60 + int(dur_secs)),
        'fps': int(fps),
        'pix_fmt': pix_fmt,
        'audio': audio_tracks,
    }
    return medio_info


def extract_frame_size(ffmpeg_parse_info: str):

    possible_patterns = [
        re.compile(r'Stream.*Video.*([0-9]{4,})x([0-9]{4,})'),
        re.compile(r'Stream.*Video.*([0-9]{4,})x([0-9]{3,})'),
        re.compile(r'Stream.*Video.*([0-9]{3,})x([0-9]{3,})')
    ]

    for pattern in possible_patterns:
        match = pattern.search(ffmpeg_parse_info)
        if match is not None:
            x, y = map(int, match.groups()[0:2])
            break

    if match is None:
        raise ValueError("could not get video frame size")

    return (x, y)


def compile_args(input_fn: str = 'pipe:',
                 output_fn: str = 'pipe:',
                 video_filters: str = [],
                 audio_filters: str = [],
                 input_options=dict(),
                 output_options=dict(),
                 overwrite_output: bool = True):
    """Wrapper for various `FFmpeg <https://www.ffmpeg.org/>`_ related applications (ffmpeg,
    ffprobe).
    """
    args = ['ffmpeg']

    input_args = []
    fmt = input_options.pop('format', None)
    if fmt:
        input_args += ['-f', fmt]

    start_time = input_options.pop('ss', None)
    duration = input_options.pop('t', None)

    input_args += kwargs_to_cmd_args(input_options)
    input_args += ['-i', input_fn]
    if start_time is not None:
        input_args += ['-ss', str(start_time)]
    if duration is not None:
        input_args += ['-t', str(duration)]

    vf_args = []
    if len(video_filters) > 0:
        vf_args = ['-vf', ','.join(video_filters)]

    af_args = []
    if len(audio_filters) > 0:
        af_args = ['-af', ','.join(audio_filters)]

    output_args = []

    fmt = output_options.pop('format', None)
    if fmt:
        output_args += ['-f', fmt]
    video_bitrate = output_options.pop('video_bitrate', None)
    if video_bitrate:
        output_args += ['-b:v', str(video_bitrate)]
    audio_bitrate = output_options.pop('audio_bitrate', None)
    if audio_bitrate:
        output_args += ['-b:a', str(audio_bitrate)]
    output_args += kwargs_to_cmd_args(output_options)

    output_args += [output_fn]

    args += input_args + vf_args + af_args + output_args

    if overwrite_output:
        args += ['-y']

    return args


def probe(input_fn: str):
    command = [
        'ffprobe', '-v', 'fatal', '-show_entries',
        'stream=width,height,r_frame_rate,duration', '-of',
        'default=noprint_wrappers=1:nokey=1', input_fn, '-sexagesimal'
    ]
    out, err = run_command(command, pipe_stdout=True, pipe_stderr=True)

    out = out.decode().split('\n')
    return {
        'file': input_fn,
        'width': int(out[0]),
        'height': int(out[1]),
        'fps': float(out[2].split('/')[0]) / float(out[2].split('/')[1]),
        'duration': out[3]
    }


def get_media_meta(input_fn: str = 'pipe:',
                   input_data: bytes = None,
                   input_options=dict()):
    _check_input(input_fn, input_data)
    cmd_args = ['ffmpeg']

    fmt = input_options.pop('format', None)
    if fmt:
        cmd_args += ['-f', fmt]
    cmd_args += ['-i', input_fn]

    cmd_args += ['-f', 'ffmetadata', 'pipe:']
    out, err = run_command(
        cmd_args, input=input_data, pipe_stdout=True, pipe_stderr=True)
    return parse_media_details(err.decode())

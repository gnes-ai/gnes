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


# def ffmpeg_probe_pattern():
#     mediaprobe_re = re.compile(
#         r"Duration:\s+(?P<dur>(?:(?:\d:?)+[.]?\d*)|N/A)(?:.+start:\s+(?P<start>\d+[.]\d+))?.+bitrate:\s+(?P<bitrate>(?:\d+\s*..[/]s)|N/A)"
#     )
#     streamprobe_re = re.compile(
#         r"\s*Stream.+:\s+Video:.+\s+(?P<res>\d+x\d+)(?:.*,\s*(?P<fps>\d+[.]?\d*)\sfps)?(?:.+\(default\))?"
#     )
#     audioprobe_re = re.compile(r"\s*Stream.+:\s+Audio:.*")
#     fftime_re = re.compile(r"(?P<h>\d+):(?P<m>\d+):(?P<s>\d+)\.(?P<fract>\d+)")


def extract_frame_size(ffmpeg_parse_info: str):
    """
    The sollution is borrowed from:
    http://concisionandconcinnity.blogspot.com/2008/04/getting-dimensions-of-video-file-in.html
    """
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

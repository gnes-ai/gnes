#  Tencent is pleased to support the open source community by making GNES available.
#
#  Copyright (C) 2019 THL A29 Limited, a Tencent company. All rights reserved.
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

# pylint: disable=low-comment-ratio


import sys

from termcolor import colored

from . import api
from .parser import get_main_parser

__all__ = ['main']


def get_run_args(parser_fn=get_main_parser, printed=True):
    parser = parser_fn()
    if len(sys.argv) > 1:
        args = parser.parse_args()
        if printed:
            param_str = '\n'.join(['%20s = %s' % (colored(k, 'yellow'), v) for k, v in sorted(vars(args).items())])
            print('usage: %s\n%s\n%s\n' % (' '.join(sys.argv), '_' * 50, param_str))
        return args
    else:
        parser.print_help()
        exit()


def main():
    args = get_run_args()
    getattr(api, args.cli, no_cli_error)(args)


def no_cli_error(*args, **kwargs):
    get_main_parser().print_help()
    exit()

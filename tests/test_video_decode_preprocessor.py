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

import os
import unittest

from gnes.cli.parser import set_preprocessor_parser, _set_client_parser
from gnes.client.base import ZmqClient
from gnes.proto import gnes_pb2, RequestGenerator, blob2array
from gnes.service.base import ServiceManager
from gnes.service.preprocessor import PreprocessorService


class TestVideoDecode(unittest.TestCase):

    def setUp(self):
        self.dirname = os.path.dirname(__file__)
        self.yml_path = os.path.join(self.dirname, 'yaml', 'preprocessor-video_decode.yml')
        self.video_path = os.path.join(self.dirname, 'videos')

    def test_video_decode_preprocessor(self):
        args = set_preprocessor_parser().parse_args(['--yaml_path', self.yml_path])
        c_args = _set_client_parser().parse_args([
            '--port_in', str(args.port_out),
            '--port_out', str(args.port_in)])
        video_bytes = [
            open(os.path.join(self.video_path, _), 'rb').read()
            for _ in os.listdir(self.video_path)
        ]

        with ServiceManager(PreprocessorService, args), ZmqClient(c_args) as client:
            for req in RequestGenerator.index(video_bytes):
                msg = gnes_pb2.Message()
                msg.request.index.CopyFrom(req.index)
                client.send_message(msg)
                r = client.recv_message()
                for d in r.request.index.docs:
                    self.assertGreater(len(d.chunks), 0)
                    for _ in range(len(d.chunks)):
                        shape = blob2array(d.chunks[_].blob).shape
                        self.assertEqual(shape, (299, 299, 3))

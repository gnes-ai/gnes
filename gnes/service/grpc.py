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


import importlib.util
import os
import sys

import grpc

from .base import BaseService as BS, MessageHandler
from ..proto import gnes_pb2


class GRPCService(BS):
    handler = MessageHandler(BS.handler)

    def post_init(self):
        self.channel = grpc.insecure_channel(
            '%s:%s' % (self.args.grpc_host, self.args.grpc_port),
            options=[('grpc.max_send_message_length', self.args.max_message_size * 1024 * 1024),
                     ('grpc.max_receive_message_length', self.args.max_message_size * 1024 * 1024)])

        foo = self.PathImport().add_modules(self.args.pb2_path, self.args.pb2_grpc_path)

        # build stub
        self.stub = getattr(foo, self.args.stub_name)(self.channel)

    def close(self):
        self.channel.close()
        super().close()

    @handler.register(NotImplementedError)
    def _handler_default(self, msg: 'gnes_pb2.Message'):
        yield getattr(self.stub, self.args.api_name)(msg)

    class PathImport:

        @staticmethod
        def get_module_name(absolute_path):
            module_name = os.path.basename(absolute_path)
            module_name = module_name.replace('.py', '')
            return module_name

        def add_modules(self, pb2_path, pb2_grpc_path):
            (module, spec) = self.path_import(pb2_path)
            sys.modules[spec.name] = module

            (module, spec) = self.path_import(pb2_grpc_path)
            sys.modules[spec.name] = module

            return module

        def path_import(self, absolute_path):
            module_name = self.get_module_name(absolute_path)
            spec = importlib.util.spec_from_file_location(module_name, absolute_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            sys.modules[spec.name] = module
            return module, spec

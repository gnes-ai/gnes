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


import zipfile

import grpc

from ..proto import gnes_pb2_grpc, RequestGenerator


class CLIClient:
    def __init__(self, args):
        if args.data_type == 'text':
            all_bytes = [v.encode() for v in args.txt_file]
        elif args.data_type == 'image':
            zipfile_ = zipfile.ZipFile(args.image_zip_file, "r")
            all_bytes = [zipfile_.open(v).read() for v in zipfile_.namelist()]
        elif args.data_type == 'video':
            raise NotImplementedError
        else:
            raise ValueError(
                '--data_type can only be text, image or video')

        with grpc.insecure_channel(
                '%s:%s' % (args.grpc_host, args.grpc_port),
                options=[('grpc.max_send_message_length', 70 * 1024 * 1024),
                         ('grpc.max_receive_message_length', 70 * 1024 * 1024)]) as channel:
            stub = gnes_pb2_grpc.GnesRPCStub(channel)

            if args.mode == 'train':
                resp = list(stub.StreamCall(RequestGenerator.train(all_bytes, args.batch_size)))[-1]
                print(resp)
            elif args.mode == 'index':
                resp = list(stub.StreamCall(RequestGenerator.train(all_bytes, args.batch_size)))[-1]
                print(resp)
            elif args.mode == 'query':
                for idx, q in enumerate(all_bytes):
                    for req in RequestGenerator.query(q, args.top_k):
                        resp = stub.Call(req)
                        print(resp)
                        print('query %d result: %s' % (idx, resp))
                        input('press any key to continue...')

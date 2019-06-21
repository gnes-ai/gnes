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


def encode(args):
    from ..service.encoder import EncoderService
    with EncoderService(args) as es:
        es.join()


def index(args):
    from ..service.indexer import IndexerService
    with IndexerService(args) as es:
        es.join()


def router(args):
    from ..service import router as my_router
    if not args.router_type:
        raise ValueError(
            '--router_type is required when starting a router from CLI')
    with getattr(my_router, args.router_type)(args) as es:
        es.join()


def frontend(args):
    from ..service.grpc import GRPCFrontend
    import threading
    with GRPCFrontend(args):
        forever = threading.Event()
        forever.wait()


def client(args):
    import grpc

    from ..proto import gnes_pb2_grpc
    from ..proto.request.text.base import TextRequestGenerator

    all_docs = [v.strip() for v in args.txt_file]
    text_req_gen = TextRequestGenerator()

    with grpc.insecure_channel(
            '%s:%s' % (args.grpc_host, args.grpc_port),
            options=[('grpc.max_send_message_length', 50 * 1024 * 1024),
                     ('grpc.max_receive_message_length', 50 * 1024 * 1024)]) as channel:
        stub = gnes_pb2_grpc.GnesRPCStub(channel)

        if args.mode == 'train':
            for req in text_req_gen.train(all_docs, args.batch_size):
                resp = stub._Call(req)
                print(resp)
        elif args.mode == 'index':
            for req in text_req_gen.index(all_docs):
                resp = stub._Call(req)
                print(resp)
        elif args.mode == 'query':
            for idx, q in enumerate(all_docs):
                for req in text_req_gen.query(q, args.top_k):
                    resp = stub._Call(req)
                    print(resp)
                    print('query %d result: %s' % (idx, resp))
                    input('press any key to continue...')


def http(args):
    from ..service.http import HttpService
    mh = HttpService(args)
    mh.start()

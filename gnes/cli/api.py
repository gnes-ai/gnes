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


def proxy(args):
    from ..service import proxy as my_proxy
    if not args.proxy_type:
        raise ValueError(
            '--proxy_type is required when starting a proxy from CLI')
    with getattr(my_proxy, args.proxy_type)(args) as es:
        es.join()


def grpc_serve(args):
    from ..service import grpc
    grpc.serve(args)


def grpc_client(args):
    import grpc
    import uuid

    from ..helper import batch_iterator
    from ..proto import gnes_pb2, gnes_pb2_grpc

    data = [v for v in args.txt_file if v.strip() if len(v) > 0]

    docs = []
    for i, line in enumerate(data):
        doc = gnes_pb2.Document()
        doc.id = i
        doc.text = line
        sents = [s.strip() for s in line.split('。') if len(s.strip()) > 0]
        doc.text_chunks.extend(sents)
        doc.doc_size = len(sents)
        doc.is_parsed = True
        docs.append(doc)

    with grpc.insecure_channel(
            '%s:%s' % (args.grpc_host, args.grpc_port),
            options=[('grpc.max_send_message_length', 50 * 1024 * 1024),
                     ('grpc.max_receive_message_length',
                      50 * 1024 * 1024)]) as channel:
        stub = gnes_pb2_grpc.GnesStub(channel)

        if args.train:
            for p in batch_iterator(docs, args.batch_size):
                req_id = str(uuid.uuid4())
                request = gnes_pb2.IndexRequest()

                request._request_id = req_id
                request.docs.extend(p)
                request.send_more = True
                request.update_model = True

                print(request._request_id)
                response = stub.Index(request)

            req_id = str(uuid.uuid4())
            request = gnes_pb2.IndexRequest()

            request._request_id = req_id
            request.update_model = True
            print(request._request_id)
            response = stub.Index(request)

            print('gnes client received: ' + str(response))
        elif args.index:
            for p in batch_iterator(docs, args.batch_size):
                req_id = str(uuid.uuid4())
                request = gnes_pb2.IndexRequest()

                request._request_id = req_id
                request.docs.extend(p)
                print(request._request_id)
                response = stub.Index(request)
                print('gnes client received: ' + str(response))
        elif args.query:
            for doc in docs[:5]:
                req_id = str(uuid.uuid4())

                # build search_request
                request = gnes_pb2.SearchRequest()
                request._request_id = req_id
                request.top_k = 5

                request.doc.CopyFrom(doc)
                print(request._request_id)
                response = stub.Search(request)
                print('gnes client received: ' + str(response))


def client(args):
    from ..service.client import ClientService
    with ClientService(args) as cs:
        data = [v for v in args.txt_file if v.strip()]
        if not data:
            raise ValueError('input text file is empty, nothing to do')
        else:
            data = [[line.strip() for line in doc.split('。') if len(line.strip()) > 3] for doc in data]

            if args.index:
                cs.index(data, args.train)
            else:
                for line in data:
                    result = cs.query(line)
                    try:
                        for _ in range(len(result.querys[0].results)):
                            print(result.querys[0].results[_].chunk.text)
                    except:
                        print('error', line, result)
        cs.join()

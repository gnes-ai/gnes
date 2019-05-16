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
        raise ValueError('--proxy_type is required when starting a proxy from CLI')
    with getattr(my_proxy, args.proxy_type)(args) as es:
        es.join()

def grpc(args):
    from ..service import grpc
    grpc.serve(args)

def client(args):
    import grpc
    import uuid

    from ..proto import gnes_pb2, gnes_pb2_grpc

    test_docs = []
    with open(args.txt_file) as f:
        title = ''
        sents = []
        doc_id = 0
        for line in f:
            line = line.strip()

            if line and not title:
                title = line
                sents.append(line)
            elif line and title:
                sents.append(line)
            elif not line and title and len(sents) > 1:
                doc = gnes_pb2.Document()
                doc.id = doc_id
                doc.text = ' '.join(sents)
                doc.text_chunks.extend(sents)
                doc.doc_size = len(sents)
                doc.is_parsed = True
                doc.is_encoded = False
                doc_id += 1
                sents.clear()
                title = ''
                test_docs.append(doc)

    with grpc.insecure_channel('%s:%s' % (args.grpc_host, args.grpc_port)) as channel:
        stub = gnes_pb2_grpc.GreeterStub(channel)

        if not args.query:
            req_id = str(uuid.uuid4())
            request = gnes_pb2.IndexRequest()

            request._request_id = req_id
            request.docs.extend(test_docs)

            if args.train:
                request.update_model = True

            response = stub.Index(request)
            print("gnes client received: " + str(response))
        else:
            pass




# def client(args):
#     from ..service.client import ClientService
#     from zmq.utils import jsonapi
#     with ClientService(args) as cs:
#         data = [v for v in args.txt_file if v.strip()]
#         if not data:
#             raise ValueError('input text file is empty, nothing to do')
#         else:
#             data = [[line.strip() for line in doc.split('。') if len(line.strip())>3] for doc in data]

#             if args.index:
#                 result = cs.index(data, args.train)
#             else:
#                 for line in data:
#                     result = cs.query(line)
#                     try:
#                         for _ in range(len(result.querys[0].results)):
#                             print(result.querys[0].results[_].chunk.text)
#                     except:
#                         print('error', line, result)
#         cs.join()


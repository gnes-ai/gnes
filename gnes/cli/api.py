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


def client(args):
    from ..service.client import ClientService
    from zmq.utils import jsonapi
    from ..helper import batch_iterator
    with ClientService(args) as cs:
        data = [v for v in args.txt_file if v.strip()]
        if not data:
            raise ValueError('input text file is empty, nothing to do')
        else:
            data = [[line.strip() for line in doc.split('。') if len(line.strip())>3] for doc in data]

            if args.index:
                if not args.train and (len(data) > args.index_batch):
                    batches = [b for b in batch_iterator(data, args.index_batch)]
                    for p_idx, b in enumerate(batches):
                        result = cs.index(b, args.train)
                else:
                    result = cs.index(data, args.train)
            else:
                for line in data:
                    result = cs.query(line)
                    try:
                        for _1 in range(len(result.querys)):
                            for _ in range(len(result.querys[_1].results)):
                                print(_1, _, result.querys[_1].results[_].chunk.text)
                    except:
                        print('error', line, result)
        cs.join()


def client_server(args):
    from ..service.client import ClientServer
    with ClientServer(args) as cs:
        cs.join()

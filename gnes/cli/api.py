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


def _start_service(cls, args):
    from ..service.base import ServiceManager
    with ServiceManager(cls, args) as es:
        es.join()


def grpc(args):
    from ..service.grpc import GRPCService
    _start_service(GRPCService, args)


def preprocess(args):
    from ..service.preprocessor import PreprocessorService
    _start_service(PreprocessorService, args)


def encode(args):
    from ..service.encoder import EncoderService
    _start_service(EncoderService, args)


def index(args):
    from ..service.indexer import IndexerService
    _start_service(IndexerService, args)


def route(args):
    from ..service.router import RouterService
    _start_service(RouterService, args)


def frontend(args):
    from ..service.frontend import FrontendService
    _start_service(FrontendService, args)


def client(args):
    if args.client == 'http':
        return _client_http(args)
    elif args.client == 'cli':
        return _client_cli(args)
    else:
        raise ValueError('gnes client must follow with a client type from {http, cli, benchmark...}\n'
                         'see "gnes client --help" for details')


def healthcheck(args):
    from ..service.base import send_ctrl_message
    from ..proto import gnes_pb2, add_version
    import time
    ctrl_addr = 'tcp://%s:%d' % (args.host, args.port)
    msg = gnes_pb2.Message()
    add_version(msg.envelope)
    msg.request.control.command = gnes_pb2.Request.ControlRequest.STATUS
    for j in range(args.retries):
        r = send_ctrl_message(ctrl_addr, msg, timeout=args.timeout)
        if not r:
            print('%s is not responding, retry (%d/%d) in 1s' % (ctrl_addr, j + 1, args.retries))
        else:
            print('%s returns %s' % (ctrl_addr, r))
            exit(0)
        time.sleep(1)
    exit(1)


def _client_http(args):
    from ..client.http import HttpClient
    HttpClient(args).start()


def _client_cli(args):
    from ..client.cli import CLIClient
    CLIClient(args)


def compose(args):
    from ..composer.base import YamlComposer
    from ..composer.flask import YamlComposerFlask
    from ..composer.http import YamlComposerHttp

    if args.flask:
        YamlComposerFlask(args).run()
    elif args.serve:
        YamlComposerHttp(args).run()
    else:
        YamlComposer(args).build_all()

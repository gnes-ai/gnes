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


import sys
import time
import zipfile
from math import ceil
from typing import List

import grpc
from termcolor import colored

from ..proto import gnes_pb2_grpc, RequestGenerator


class CLIClient:
    def __init__(self, args):
        if args.txt_file:
            all_bytes = [v.encode() for v in args.txt_file]
        elif args.image_zip_file:
            zipfile_ = zipfile.ZipFile(args.image_zip_file)
            all_bytes = [zipfile_.open(v).read() for v in zipfile_.namelist()]
        elif args.video_zip_file:
            zipfile_ = zipfile.ZipFile(args.video_zip_file)
            all_bytes = [zipfile_.open(v).read() for v in zipfile_.namelist()]
        else:
            raise AttributeError('--txt_file, --image_zip_file, --video_zip_file one must be given')

        with grpc.insecure_channel(
                '%s:%s' % (args.grpc_host, args.grpc_port),
                options=[('grpc.max_send_message_length', args.max_message_size * 1024 * 1024),
                         ('grpc.max_receive_message_length', args.max_message_size * 1024 * 1024)]) as channel:
            stub = gnes_pb2_grpc.GnesRPCStub(channel)

            if args.mode == 'train':
                with ProgressBar(all_bytes, args.batch_size, task_name=args.mode) as p_bar:
                    for _ in stub.StreamCall(RequestGenerator.train(all_bytes,
                                                                    start_doc_id=args.start_doc_id,
                                                                    batch_size=args.batch_size)):
                        p_bar.update()
            elif args.mode == 'index':
                with ProgressBar(all_bytes, args.batch_size, task_name=args.mode) as p_bar:
                    for _ in stub.StreamCall(RequestGenerator.index(all_bytes,
                                                                    start_doc_id=args.start_doc_id,
                                                                    batch_size=args.batch_size)):
                        p_bar.update()
            elif args.mode == 'query':
                for idx, q in enumerate(all_bytes):
                    for req in RequestGenerator.query(q, start_request_id=idx, top_k=args.top_k):
                        resp = stub.Call(req)
                        print(resp)
                        print('query %d result: %s' % (idx, resp))
                        input('press any key to continue...')


class ProgressBar:
    def __init__(self, all_bytes: List[bytes], batch_size: int, bar_len: int = 20, task_name: str = ''):
        self.all_bytes_len = [len(v) for v in all_bytes]
        self.batch_size = batch_size
        self.total_batch = ceil(len(self.all_bytes_len) / self.batch_size)
        self.bar_len = bar_len
        self.task_name = task_name

    def update(self):
        if self.num_batch > self.total_batch - 1:
            return
        sys.stdout.write('\r')
        elapsed = time.perf_counter() - self.start_time
        elapsed_str = colored('elapsed', 'yellow')
        speed_str = colored('speed', 'yellow')
        self.num_batch += 1
        percent = self.num_batch / self.total_batch
        num_bytes = sum(self.all_bytes_len[((self.num_batch - 1) * self.batch_size):(self.num_batch * self.batch_size)])
        sys.stdout.write(
            '{:>10} [{:<{}}] {:3.0f}%   {:>10}: {:3.1f}s   {:>10}: {:3.1f} bytes/s'.format(
                colored(self.task_name, 'cyan'),
                colored('=' * int(self.bar_len * percent), 'green'),
                self.bar_len + 9,
                percent * 100,
                elapsed_str,
                elapsed,
                speed_str,
                num_bytes / elapsed
            ))
        sys.stdout.flush()

    def __enter__(self):
        self.start_time = time.perf_counter()
        self.num_batch = 0
        sys.stdout.write('\n')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.write('\n')

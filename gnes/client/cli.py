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

from termcolor import colored

from .base import GrpcClient
from ..proto import RequestGenerator, gnes_pb2


class CLIClient(GrpcClient):
    def __init__(self, args):
        super().__init__(args)
        getattr(self, self.args.mode)(self.read_all())
        self.close()

    def train(self, all_bytes: List[bytes]):
        with ProgressBar(all_bytes, self.args.batch_size, task_name=self.args.mode) as p_bar:
            for _ in self._stub.StreamCall(RequestGenerator.train(all_bytes,
                                                                  doc_id_start=self.args.start_doc_id,
                                                                  batch_size=self.args.batch_size)):
                p_bar.update()

    def index(self, all_bytes: List[bytes]):
        with ProgressBar(all_bytes, self.args.batch_size, task_name=self.args.mode) as p_bar:
            for _ in self._stub.StreamCall(RequestGenerator.index(all_bytes,
                                                                  doc_id_start=self.args.start_doc_id,
                                                                  batch_size=self.args.batch_size)):
                p_bar.update()

    def query(self, all_bytes: List[bytes]):
        for idx, q in enumerate(all_bytes):
            for req in RequestGenerator.query(q, request_id_start=idx, top_k=self.args.top_k):
                resp = self._stub.Call(req)
                self.query_callback(req, resp)

    def query_callback(self, req: 'gnes_pb2.Request', resp: 'gnes_pb2.Response'):
        """
        callback after get the query result
        override this method to customize query behavior
        :param resp: response
        :param req: query
        :return:
        """
        print(req)
        print(resp)

    def read_all(self) -> List[bytes]:
        if self.args.txt_file:
            all_bytes = [v.encode() for v in self.args.txt_file]
        elif self.args.image_zip_file:
            zipfile_ = zipfile.ZipFile(self.args.image_zip_file)
            all_bytes = [zipfile_.open(v).read() for v in zipfile_.namelist()]
        elif self.args.video_zip_file:
            zipfile_ = zipfile.ZipFile(self.args.video_zip_file)
            all_bytes = [zipfile_.open(v).read() for v in zipfile_.namelist()]
        else:
            raise AttributeError('--txt_file, --image_zip_file, --video_zip_file one must be given')

        return all_bytes


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
        estleft_str = colored('left', 'yellow')
        self.num_batch += 1
        percent = self.num_batch / self.total_batch
        num_bytes = sum(self.all_bytes_len[((self.num_batch - 1) * self.batch_size):(self.num_batch * self.batch_size)])
        sys.stdout.write(
            '{:>10} [{:<{}}] {:3.0f}%   {:>8}: {:3.1f}s   {:>8}: {:3.1f} bytes/s  {:3.1f} batch/s {:>8}: {:3.1f}s'.format(
                colored(self.task_name, 'cyan'),
                colored('=' * int(self.bar_len * percent), 'green'),
                self.bar_len + 9,
                percent * 100,
                elapsed_str,
                elapsed,
                speed_str,
                num_bytes / elapsed,
                self.num_batch / elapsed,
                estleft_str,
                (self.total_batch - self.num_batch) / ((self.num_batch + 0.0001) / elapsed)
            ))
        sys.stdout.flush()

    def __enter__(self):
        self.start_time = time.perf_counter()
        self.num_batch = -1
        sys.stdout.write('\n')
        self.update()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.write('\t%s\n' % colored('done!', 'green'))

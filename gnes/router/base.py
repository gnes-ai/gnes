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
from typing import List, Optional, Generator

from ..base import TrainableBase
from ..proto import gnes_pb2, merge_routes


class BaseRouter(TrainableBase):
    def apply(self, msg: 'gnes_pb2.Message', *args, **kwargs):
        pass


class BaseMapRouter(BaseRouter):
    def apply(self, msg: 'gnes_pb2.Message', *args, **kwargs) -> Generator:
        pass


class BaseReduceRouter(BaseRouter):
    def apply(self, msg: 'gnes_pb2.Message', accum_msgs: List['gnes_pb2.Message'], *args, **kwargs) -> None:
        merge_routes(msg, accum_msgs)
        msg.envelope.num_part = 1

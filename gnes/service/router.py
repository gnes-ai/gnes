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

from collections import defaultdict
from typing import Dict, List

from .base import BaseService as BS, MessageHandler, BlockMessage
from ..proto import gnes_pb2
from ..router.base import BaseReduceRouter


class RouterService(BS):
    handler = MessageHandler(BS.handler)

    def post_init(self):
        from ..router.base import BaseRouter
        self._model = self.load_model(BaseRouter)
        self._pending = defaultdict(list)  # type: Dict[str, List]

    def _is_msg_complete(self, msg: 'gnes_pb2.Message', num_req: int) -> bool:
        return (hasattr(self.args, 'num_part') and num_req == self.args.num_part) or (num_req == msg.envelope.num_part)

    @handler.register(NotImplementedError)
    def _handler_default(self, msg: 'gnes_pb2.Message'):
        if isinstance(self._model, BaseReduceRouter):
            req_id = msg.envelope.request_id
            self._pending[req_id].append(msg)
            num_req = len(self._pending[req_id])

            if self._is_msg_complete(msg, num_req):
                prev_msgs = self._pending.pop(req_id)
                return self._model.apply(msg, prev_msgs)
            else:
                raise BlockMessage
        else:
            return self._model.apply(msg)

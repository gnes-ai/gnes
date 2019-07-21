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

from typing import List

import numpy as np

from ..base import BaseReduceRouter
from ...proto import gnes_pb2, blob2array, array2blob


class ConcatEmbedRouter(BaseReduceRouter):

    def apply(self, msg: 'gnes_pb2.Message', accum_msgs: List['gnes_pb2.Message'], *args, **kwargs):
        body = getattr(msg, msg.WhichOneof('body'))
        msg_type = type(getattr(body, body.WhichOneof('body')))
        if msg_type == gnes_pb2.Request.QueryRequest:
            msg.request.search.query.chunk_embeddings.CopyFrom(array2blob(
                np.concatenate([blob2array(m.request.search.query.chunk_embeddings) for m in accum_msgs], axis=1)))
        elif msg_type == gnes_pb2.Request.IndexRequest:
            for i in range(len(msg.request.index.docs)):
                msg.request.index.docs[i].chunk_embeddings.CopyFrom(array2blob(
                    np.concatenate([blob2array(m.request.index.docs[i].chunk_embeddings) for m in accum_msgs], axis=1)))
        else:
            self.logger.error('dont know how to handle %s' % msg_type)

        super().apply(msg, accum_msgs)

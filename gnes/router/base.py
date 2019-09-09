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
from collections import defaultdict
from typing import List, Generator

from gnes.score_fn.base import CombinedScoreFn
from ..base import TrainableBase, CompositionalTrainableBase
from ..proto import gnes_pb2, merge_routes, array2blob


class BaseRouter(TrainableBase):
    """ Base class for the router. Inherit from this class to create a new router.

    Router forwards messages between services. Essentially, it receives a 'gnes_pb2.Message'
    and call `apply()` method on it.
    """

    def apply(self, msg: 'gnes_pb2.Message', *args, **kwargs):
        """
        Modify the incoming message

        :param msg: incoming message
        """
        pass


class BaseMapRouter(BaseRouter):
    def apply(self, msg: 'gnes_pb2.Message', *args, **kwargs) -> Generator:
        pass


class BaseReduceRouter(BaseRouter):
    def apply(self, msg: 'gnes_pb2.Message', accum_msgs: List['gnes_pb2.Message'], *args, **kwargs) -> None:
        """
        Modify the current message based on accumulated messages

        :param msg: the current message
        :param accum_msgs: accumulated messages
        """
        merge_routes(msg, accum_msgs)
        if len(msg.envelope.num_part) > 1:
            msg.envelope.num_part.pop()
        else:
            self.logger.warning(
                'message envelope says num_part=%s, means no further message reducing. '
                'ignore this if you explicitly set "num_part" in RouterService' % msg.envelope.num_part)


class BaseTopkReduceRouter(BaseReduceRouter):
    def __init__(self, reduce_op: str = 'sum', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._reduce_op = reduce_op

    def post_init(self):
        self.reduce_op = CombinedScoreFn(score_mode=self._reduce_op)

    def get_key(self, x: 'gnes_pb2.Response.QueryResponse.ScoredResult') -> str:
        raise NotImplementedError

    def set_key(self, x: 'gnes_pb2.Response.QueryResponse.ScoredResult', k: str) -> None:
        raise NotImplementedError

    def apply(self, msg: 'gnes_pb2.Message', accum_msgs: List['gnes_pb2.Message'], *args, **kwargs):
        # now convert chunk results to doc results
        all_scored_results = [sr for m in accum_msgs for sr in m.response.search.topk_results]
        score_dict = defaultdict(list)

        # count score by iterating over chunks
        for c in all_scored_results:
            score_dict[self.get_key(c)].append(c.score)

        for k, v in score_dict.items():
            score_dict[k] = self.reduce_op(*v)

        msg.response.search.ClearField('topk_results')

        for k, v in score_dict.items():
            r = msg.response.search.topk_results.add()
            r.score.CopyFrom(v)
            self.set_key(r, k)

        super().apply(msg, accum_msgs)


class BaseEmbedReduceRouter(BaseReduceRouter):
    def reduce_embedding(self, accum_msgs: List['gnes_pb2.Message'], msg_type: str, chunk_idx: int, doc_idx: int):
        raise NotImplementedError

    def apply(self, msg: 'gnes_pb2.Message', accum_msgs: List['gnes_pb2.Message'], *args, **kwargs) -> None:
        """
        reduce embeddings from encoders (means, concat ....)
        :param msg: the current message
        :param accum_msgs: accumulated messages
        """
        body = getattr(msg, msg.WhichOneof('body'))
        msg_type = type(getattr(body, body.WhichOneof('body')))
        if msg_type == gnes_pb2.Request.QueryRequest:
            for i in range(len(msg.request.search.query.chunks)):
                reduced_embedding = array2blob(self.reduce_embedding(accum_msgs, 'query', chunk_idx=i, doc_idx=-1))
                msg.request.search.query.chunks[i].embedding.CopyFrom(reduced_embedding)
        elif msg_type == gnes_pb2.Request.IndexRequest:
            for i in range(len(msg.request.index.docs)):
                for j in range(len(msg.request.index.docs[i].chunks)):
                    reduced_embedding = array2blob(self.reduce_embedding(accum_msgs, 'index', chunk_idx=j, doc_idx=i))
                    msg.request.index.docs[i].chunks[j].embedding.CopyFrom(reduced_embedding)
        else:
            self.logger.error('dont know how to handle %s' % msg_type)

        super().apply(msg, accum_msgs)


class PipelineRouter(CompositionalTrainableBase):
    def apply(self, *args, **kwargs) -> None:
        if not self.components:
            raise NotImplementedError
        for be in self.components:
            be.apply(*args, **kwargs)

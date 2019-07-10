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

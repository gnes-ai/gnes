from collections import defaultdict
from typing import List

from ..base import BaseReduceRouter
from ...proto import gnes_pb2


class ChunkReduceRouter(BaseReduceRouter):

    def apply(self, msg: 'gnes_pb2.Message', accum_msgs: List['gnes_pb2.Message'], *args, **kwargs):
        all_chunks = [r for m in accum_msgs for r in m.response.search.topk_results]
        doc_score = defaultdict(float)
        doc_score_explained = defaultdict(str)

        # count score by iterating over chunks
        for c in all_chunks:
            doc_score[c.chunk.doc_id] += c.score
            doc_score_explained[c.chunk.doc_id] += '%s\n' % c.score_explained

        # now convert chunk results to doc results
        msg.response.search.level = gnes_pb2.Response.QueryResponse.DOCUMENT_NOT_FILLED
        msg.response.search.ClearField('topk_results')

        # sort and add docs
        for k, v in sorted(doc_score.items(), key=lambda kv: -kv[1]):
            r = msg.response.search.topk_results.add()
            r.doc.doc_id = k
            r.score = v
            r.score_explained = doc_score_explained[k]

        super().apply(msg, accum_msgs)

from typing import List

from ..base import BaseReduceRouter
from ...proto import gnes_pb2


class DocReduceRouter(BaseReduceRouter):
    def apply(self, msg: 'gnes_pb2.Message', accum_msgs: List['gnes_pb2.Message'], *args, **kwargs):
        final_docs = []
        for idx, r in enumerate(msg.response.search.topk_results):
            # get result from all shards, some may return None, we only take the first non-None doc
            final_docs.append([m.response.search.topk_results[idx] for m in accum_msgs if
                               m.response.search.topk_results[idx].doc.WhichOneof('raw_data') is not None][0])

        # resort all doc result as the doc_weight has been applied
        final_docs = sorted(final_docs, key=lambda x: x.score, reverse=True)
        msg.response.search.ClearField('topk_results')
        msg.response.search.topk_results.extend(final_docs[:msg.response.search.top_k])

        super().apply(msg, accum_msgs)

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
from typing import List

from ..base import TrainableBase
from ..proto import gnes_pb2, merge_routes


class BasePostprocessor(TrainableBase):

    def apply(self, msg: 'gnes_pb2.Message', prev_msgs: List['gnes_pb2.Message']):
        merge_routes(msg, prev_msgs)


class BaseChunkPostprocessor(BasePostprocessor):

    def apply(self, msg: 'gnes_pb2.Message', prev_msgs: List['gnes_pb2.Message']):
        all_chunks = [r for m in prev_msgs for r in m.response.search.topk_results]
        doc_score = defaultdict(float)
        doc_score_explained = defaultdict(str)

        # count score by iterating over chunks
        for c in all_chunks:
            doc_score[c.chunk.doc_id] += c.score
            doc_score_explained += '%s\n' % c.score_explained

        # now convert chunk results to doc results
        msg.response.search.level = gnes_pb2.Response.QueryResponse.DOCUMENT_NOT_FILLED
        msg.response.search.ClearField('topk_results')

        # sort and add docs
        for k, v in sorted(doc_score.items(), key=lambda kv: -kv[1]):
            r = msg.response.search.topk_results.add()
            r.doc = gnes_pb2.Document()
            r.doc.doc_id = k
            r.score = v
            r.score_explained = doc_score_explained[k]

        super().apply(msg, prev_msgs)


class BaseDocPostprocessor(BasePostprocessor):

    def apply(self, msg: 'gnes_pb2.Message', prev_msgs: List['gnes_pb2.Message']):
        final_docs = []
        for r, idx in enumerate(msg.response.search.topk_results):
            # get result from all shards, some may return None, we only take the first non-None doc
            final_docs.append([r for m in prev_msgs if
                               m.response.search.topk_results[idx].doc.WhichOneOf('raw_data') is not None][0])

        # resort all doc result as the doc_weight has been applied
        final_docs = sorted(final_docs, key=lambda x: x.score, reverse=True)
        msg.response.search.ClearField('topk_results')
        msg.response.search.topk_results.extend(final_docs[:msg.response.search.top_k])

        super().apply(msg, prev_msgs)

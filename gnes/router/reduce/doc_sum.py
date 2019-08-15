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
from typing import List

from ..base import BaseReduceRouter
from ...proto import gnes_pb2


class DocSumRouter(BaseReduceRouter):
    def apply(self, msg: 'gnes_pb2.Message', accum_msgs: List['gnes_pb2.Message'], *args, **kwargs):
        final_fulltext_docs = []

        all_docs = [top_k.doc for m in accum_msgs for top_k in m.response.search.topk_results]
        all_docs_socres = [top_k.score for m in accum_msgs for top_k in m.response.search.topk_results]
        all_score_explained = [top_k.score_explained for m in accum_msgs for top_k in m.response.search.topk_results]

        doc_id = defaultdict(gnes_pb2.Document)
        doc_score = defaultdict(float)
        doc_score_explained = defaultdict(str)

        for d, s, ex in zip(all_docs, all_docs_socres, all_score_explained):
            doc_id[d.doc_id] = d
            doc_score[d.doc_id] += s
            doc_score_explained[d.doc_id] += '%s\n' % ex

        msg.response.search.ClearField('topk_results')

        # sort and add docs
        for k, v in sorted(doc_score.items(), key=lambda kv: -kv[1]):
            r = msg.response.search.topk_results.add()
            r.doc.CopyFrom(doc_id[k])
            r.score = v
            r.score_explained = doc_score_explained[k]
            final_fulltext_docs.append(r)

        # resort all doc result as the doc_weight has been applied
        final_fulltext_docs = sorted(final_fulltext_docs, key=lambda x: x.score, reverse=True)
        msg.response.search.ClearField('topk_results')
        msg.response.search.topk_results.extend(final_fulltext_docs[:msg.response.search.top_k])

        super().apply(msg, accum_msgs)

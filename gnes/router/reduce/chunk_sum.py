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


class ChunkSumRouter(BaseReduceRouter):
    def apply(self, msg: 'gnes_pb2.Message', accum_msgs: List['gnes_pb2.Message'], *args, **kwargs):
        all_docs_id = [top_k.doc.doc_id for m in accum_msgs for top_k in m.response.search.topk_results]
        all_docs_socres = [top_k.score for m in accum_msgs for top_k in m.response.search.topk_results]
        all_score_explained = [top_k.score_explained for m in accum_msgs for top_k in m.response.search.topk_results]

        doc_score = defaultdict(float)
        doc_score_explained = defaultdict(str)

        for id_, s, ex in zip(all_docs_id, all_docs_socres, all_score_explained):
            doc_score[id_] += s
            doc_score_explained[id_] += '%s\n' % ex

        msg.response.search.ClearField('topk_results')

        # sort and add docs
        for k, v in sorted(doc_score.items(), key=lambda kv: -kv[1]):
            r = msg.response.search.topk_results.add()
            r.doc.doc_id = k
            r.score = v
            r.score_explained = doc_score_explained[k]

        super().apply(msg, accum_msgs)

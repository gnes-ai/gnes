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

from ..base import BaseReduceRouter
from ...proto import gnes_pb2


class DocFillRouter(BaseReduceRouter):
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

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

from .base import get_unary_score, CombinedScoreFn
import json


class WeightedDocScoreFn(CombinedScoreFn):
    def __call__(self, last_score: 'gnes_pb2.Response.QueryResponse.ScoredResult.Score',
                 doc: 'gnes_pb2.Document', *args, **kwargs):
        d_weight = get_unary_score(value=doc.weight,
                                   name='doc weight',
                                   doc_id=doc.doc_id)
        return super().__call__(last_score, d_weight)


class CoordDocScoreFn(CombinedScoreFn):
    """
    score = score * query_coordination
    query_coordination: #chunks recalled / #chunks in this doc
    """

    def __call__(self, last_score: 'gnes_pb2.Response.QueryResponse.ScoredResult.Score',
                 doc: 'gnes_pb2.Document',
                 *args, **kwargs):
        total_chunks = len(doc.chunks)
        recall_chunks = len(json.loads(last_score.explained)['operands'])
        query_coord = 1 if total_chunks == 0 else recall_chunks / total_chunks
        d_weight = get_unary_score(value=query_coord,
                                   name='query coordination')
        return super().__call__(last_score, d_weight)


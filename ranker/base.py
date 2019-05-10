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


from typing import List, Any

import numpy as np

from ..base import TrainableBase


class BaseRanker(TrainableBase):
    def ranking(self, data: Any, *args, **kwargs) -> Any:
        pass


class ReduceRanker(TrainableBase):
    def __init__(self, reduce_method='mean_count', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reduce_method = reduce_method
        self.reduce_handler = {'mean': np.mean,
                               'max': np.max,
                               'count': len,
                               'mean_count': lambda x: np.mean(x)*np.log(len(x)),
                               'max_count': lambda x: np.max(x)*np.log(len(x))}

    def ranking(self, doc_ids: List[int], scores: List[float], *args, **kwargs) -> Any:
        id_count = {}
        result = []
        for doc_id, score in zip(doc_ids, scores):
            if doc_id in id_count:
                id_count[doc_id].append(score)
            else:
                id_count[doc_id] = [score]

        for k, v in id_count.items():
            result.append((k, self.reduce_handler[self.reduce_method](v)))

        result = sorted(result, key=lambda x: -x[1])
        return result

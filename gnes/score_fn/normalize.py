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

from .base import ModifierScoreFn, ScoreOps as so


class Normalizer1(ModifierScoreFn):
    """Do normalizing: score = 1 / (1 + sqrt(score))"""

    def __init__(self):
        super().__init__(modifier='reciprocal1p')

    def __call__(self, last_score, *args, **kwargs):
        return super().__call__(so.sqrt(last_score))


class Normalizer2(ModifierScoreFn):
    """Do normalizing: score = 1 / (1 + score / num_dim)"""

    def __init__(self, num_dim: int):
        super().__init__(modifier='reciprocal1p', factor=1.0 / num_dim, factor_name='1/num_dim')


class Normalizer3(Normalizer2):
    """Do normalizing: score = 1 / (1 + sqrt(score) / num_dim)"""

    def __call__(self, last_score, *args, **kwargs):
        return super().__call__(so.sqrt(last_score))


class Normalizer4(ModifierScoreFn):
    """Do normalizing: score = 1 - score / num_bytes """

    def __init__(self, num_bytes: int):
        super().__init__(modifier='invert1p', factor=1.0 / num_bytes, factor_name='1/num_bytes')


class Normalizer5(ModifierScoreFn):
    """Do normalizing: score = 1 / (1 + sqrt(abs(score)))"""

    def __init__(self):
        super().__init__(modifier='reciprocal1p')

    def __call__(self, last_score, *args, **kwargs):
        return super().__call__(so.sqrt(so.abs(last_score)))

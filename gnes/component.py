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

from .encoder import base as encoder_base
from .indexer import base as indexer_base
from .preprocessor import base as prep_base
from .router import base as router_base
from .score_fn import base as score_base

# Encoder
BaseEncoder = encoder_base.BaseEncoder
BaseTextEncoder = encoder_base.BaseTextEncoder
BaseAudioEncoder = encoder_base.BaseAudioEncoder
BaseImageEncoder = encoder_base.BaseImageEncoder
BaseVideoEncoder = encoder_base.BaseVideoEncoder
BaseBinaryEncoder = encoder_base.BaseBinaryEncoder
BaseNumericEncoder = encoder_base.BaseNumericEncoder
PipelineEncoder = encoder_base.PipelineEncoder

# Indexer
BaseChunkIndexer = indexer_base.BaseChunkIndexer
BaseIndexer = indexer_base.BaseIndexer
BaseDocIndexer = indexer_base.BaseDocIndexer
BaseKeyIndexer = indexer_base.BaseChunkIndexerHelper
JointIndexer = indexer_base.JointIndexer

# Preprocessor
BasePreprocessor = prep_base.BasePreprocessor
BaseImagePreprocessor = prep_base.BaseImagePreprocessor
BaseTextPreprocessor = prep_base.BaseTextPreprocessor
BaseAudioPreprocessor = prep_base.BaseAudioPreprocessor
BaseVideoPreprocessor = prep_base.BaseVideoPreprocessor
PipelinePreprocessor = prep_base.PipelinePreprocessor
UnaryPreprocessor = prep_base.UnaryPreprocessor

# Router
BaseReduceRouter = router_base.BaseReduceRouter
BaseRouter = router_base.BaseRouter
BaseTopkReduceRouter = router_base.BaseTopkReduceRouter
BaseMapRouter = router_base.BaseMapRouter
PipelineRouter = router_base.PipelineRouter

# Score_Fn
BaseScoreFn = score_base.BaseScoreFn
ModifierScoreFn = score_base.ModifierScoreFn
CombinedScoreFn = score_base.CombinedScoreFn

from .encoder import base as encoder_base
from .indexer import base as indexer_base
from .preprocessor import base as prep_base
from .router import base as router_base

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
BaseKeyIndexer = indexer_base.BaseKeyIndexer
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

from . import Flow

# these base flow define common topology in real world
# however, they are not usable directly unless you set the correct `yaml_path`

BaseIndexFlow = (Flow()
                 .add_preprocessor(name='prep', yaml_path='BasePreprocessor')
                 .add_encoder(name='enc', yaml_path='BaseEncoder')
                 .add_indexer(name='vec_idx', yaml_path='BaseIndexer')
                 .add_indexer(name='doc_idx', yaml_path='BaseIndexer', recv_from='prep')
                 .add_router(name='sync', yaml_path='BaseReduceRouter',
                             num_part=2, recv_from=['vec_idx', 'doc_idx']))

BaseQueryFlow = (Flow()
                 .add_preprocessor(name='prep', yaml_path='BasePreprocessor')
                 .add_encoder(name='enc', yaml_path='BaseEncoder')
                 .add_indexer(name='vec_idx', yaml_path='BaseIndexer')
                 .add_router(name='scorer', yaml_path='Chunk2DocTopkReducer')
                 .add_indexer(name='doc_idx', yaml_path='BaseIndexer'))

from . import Flow


class BaseIndexFlow(Flow):
    """
    BaseIndexFlow defines a common service pipeline when indexing.

    It can not be directly used as all services are using the base module by default.
    You have to use :py:meth:`set` to change the `yaml_path` of each service.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        (self.add_preprocessor(name='prep', yaml_path='BasePreprocessor', copy_flow=False)
         .add_encoder(name='enc', yaml_path='BaseEncoder', copy_flow=False)
         .add_indexer(name='vec_idx', yaml_path='BaseIndexer', copy_flow=False)
         .add_indexer(name='doc_idx', yaml_path='BaseIndexer', recv_from='prep', copy_flow=False)
         .add_router(name='sync', yaml_path='BaseReduceRouter',
                     num_part=2, recv_from=['vec_idx', 'doc_idx'], copy_flow=False))


class BaseQueryFlow(Flow):
    """
    BaseIndexFlow defines a common service pipeline when indexing.

    It can not be directly used as all services are using the base module by default.
    You have to use :py:meth:`set` to change the `yaml_path` of each service.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        (self.add_preprocessor(name='prep', yaml_path='BasePreprocessor', copy_flow=False)
         .add_encoder(name='enc', yaml_path='BaseEncoder', copy_flow=False)
         .add_indexer(name='vec_idx', yaml_path='BaseIndexer', copy_flow=False)
         .add_router(name='scorer', yaml_path='Chunk2DocTopkReducer', copy_flow=False)
         .add_indexer(name='doc_idx', yaml_path='BaseIndexer', copy_flow=False))

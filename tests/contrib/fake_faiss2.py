from gnes.indexer.base import BaseVectorIndexer


class FaissIndexer(BaseVectorIndexer):

    def __init__(self, bar: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_trained = True
        self.bar = bar
        self.logger.info('look at me, I override the overrided faiss indexer!!!')


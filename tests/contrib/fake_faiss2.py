from gnes.indexer.base import BaseChunkIndexer


class FaissIndexer(BaseChunkIndexer):

    def __init__(self, bar: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_trained = True
        self.bar = bar
        self.logger.info('look at me, I override the overrided faiss indexer!!!')

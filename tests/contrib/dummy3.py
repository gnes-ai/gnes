from gnes.component import BaseEncoder
from gnes.helper import train_required


class DummyEncoder3(BaseEncoder):

    def train(self, *args, **kwargs):
        self.logger.info('you just trained me!')
        pass

    @train_required
    def encode(self, x):
        return x + 1

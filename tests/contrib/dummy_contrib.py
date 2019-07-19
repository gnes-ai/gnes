from gnes.encoder.base import BaseTextEncoder


class FooContribEncoder(BaseTextEncoder):

    def __init__(self, bar: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_trained = True
        self.bar = bar

    def encode(self, text, **kwargs):
        return 'hello %d' % self.bar

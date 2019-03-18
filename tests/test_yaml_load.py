import unittest

from src.nes.base import TrainableType


class foo(metaclass=TrainableType):
    def __init__(self, *args, **kwargs):
        pass

    def close(self):
        pass


class foo1(foo):
    def __init__(self, a, b=1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pass


class foo2(foo1):
    def __init__(self, c, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pass


class TestYamlLoad(unittest.TestCase):

    def test_siganature(self):
        a = foo1(2)
        self.assertEqual(a._init_kwargs_dict, {'a': 2, 'b': 1})
        a = foo2(2, 3, 3)
        self.assertEqual(a._init_kwargs_dict, {'c': 2, 'a': 3, 'b': 3})
        self.assertRaises(TypeError, foo2, 2, 3, c=2)
        a = foo2(2, 3, 4, 5, 6, 7)
        self.assertEqual(a._init_kwargs_dict, {'c': 2, 'a': 3, 'b': 4})
        a = foo2(2, 3, wee=4)
        self.assertEqual(a._init_kwargs_dict, {'c': 2, 'a': 3, 'b': 1})
        a = foo2(b=1, wee=4, a=3, c=2)
        self.assertEqual(a._init_kwargs_dict, {'c': 2, 'a': 3, 'b': 1})

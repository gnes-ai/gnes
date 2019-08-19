import os
import unittest
from shutil import rmtree

from gnes.base import TrainableType
from gnes.encoder.base import PipelineEncoder
from gnes.encoder.numeric.pca import PCALocalEncoder
from gnes.encoder.numeric.pq import PQEncoder
from gnes.encoder.numeric.tf_pq import TFPQEncoder


class foo(metaclass=TrainableType):
    def __init__(self, *args, **kwargs):
        pass

    def close(self):
        pass


class foo1(foo):
    store_args_kwargs = False

    def __init__(self, a, b=1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pass


class foo2(foo1):
    def __init__(self, c, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pass


class dummyPipeline(PipelineEncoder):
    store_args_kwargs = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.components = lambda: [foo1(*args, **kwargs),
                                   foo2(*args, **kwargs), ]


class TestYaml(unittest.TestCase):
    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'dump.yml')
        self.db_path = './test_leveldb'

    def tearDown(self):
        if os.path.exists(self.db_path):
            rmtree(self.db_path)
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)

    def test_signature(self):
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

    def test_dump(self):
        pe0 = dummyPipeline(a=23, b=32, c=['123', '456'])
        pe0.dump_yaml(self.dump_path)
        self.assertTrue(os.path.exists(self.dump_path))
        pe = dummyPipeline.load_yaml(self.dump_path)
        self.assertEqual(type(pe), dummyPipeline)
        self.assertEqual(pe0._init_kwargs_dict, pe._init_kwargs_dict)

    def test_dump2(self):
        dummyPipeline.store_args_kwargs = False
        pe0 = dummyPipeline(a=23, b=32, c=['123', '456'])
        self.assertEqual(pe0._init_kwargs_dict, {})
        dummyPipeline.store_args_kwargs = True
        pe0 = dummyPipeline(a=23, b=32, c=['123', '456'])
        self.assertEqual(pe0._init_kwargs_dict, {'kwargs': dict(a=23, b=32, c=['123', '456'])})
        pe0.dump_yaml(self.dump_path)
        self.assertTrue(os.path.exists(self.dump_path))
        dummyPipeline.store_args_kwargs = False
        pe = dummyPipeline.load_yaml(self.dump_path)
        self.assertEqual(type(pe), dummyPipeline)
        self.assertEqual(pe._init_kwargs_dict, {})
        dummyPipeline.store_args_kwargs = True

    def test_load(self):
        with open(self.dump_path, 'w') as fp:
            fp.write("!PipelineEncoder\n\
                                parameters:\n\
                                  kwargs:\n\
                                    a: 23\n\
                                    b: '32'\n\
                                    c: ['123', '456']")
        PipelineEncoder.store_args_kwargs = True
        pe = dummyPipeline.load_yaml(self.dump_path)
        self.assertEqual(type(pe), PipelineEncoder)
        self.assertEqual(pe._init_kwargs_dict, {'kwargs': dict(a=23, b=32, c=['123', '456'])})
        PipelineEncoder.store_args_kwargs = False
        pe = dummyPipeline.load_yaml(self.dump_path)
        self.assertEqual(type(pe), PipelineEncoder)
        self.assertEqual(pe._init_kwargs_dict, {})

        with open(self.dump_path, 'w') as fp:
            fp.write("!PipelineEncoder\n\
                                parameters:\n\
                                  args:\n\
                                    - 23\n\
                                    - '32'\n\
                                    - ['123', '456']")
        PipelineEncoder.store_args_kwargs = True
        pe = dummyPipeline.load_yaml(self.dump_path)
        self.assertEqual(type(pe), PipelineEncoder)
        self.assertEqual(pe._init_kwargs_dict, {'args': (23, 32, ['123', '456'])})

        PipelineEncoder.store_args_kwargs = False
        pe = dummyPipeline.load_yaml(self.dump_path)
        self.assertEqual(type(pe), PipelineEncoder)
        self.assertEqual(pe._init_kwargs_dict, {})

    def test_nest_pipeline(self):
        self._test_different_encoder_yamlize(dummyPipeline, a=1, b=2, c=3, wee=4)
        self._test_different_encoder_yamlize(PQEncoder, 10)
        self._test_different_encoder_yamlize(TFPQEncoder, 10)
        self._test_different_encoder_yamlize(PCALocalEncoder, 20, 10)

    def _test_different_encoder_yamlize(self, cls, *args, **kwargs):
        a = cls(*args, **kwargs)
        a.dump_yaml(self.dump_path)
        a.close()
        self.assertTrue(os.path.exists(self.dump_path))
        b = cls.load_yaml(self.dump_path)
        self.assertEqual(type(b), cls)
        self.assertEqual(a._init_kwargs_dict, b._init_kwargs_dict)
        b.close()

    @unittest.SkipTest
    def test_NES_yaml_dump(self):
        self._test_different_encoder_yamlize(GNES, num_bytes=8,
                                             pca_output_dim=32,
                                             cluster_per_byte=8,
                                             port=1,
                                             port_out=2,
                                             data_path=self.db_path,
                                             ignore_all_checks=True)

    @unittest.SkipTest
    def test_double_dump(self):
        a = GNES(num_bytes=8,
                 pca_output_dim=32,
                 cluster_per_byte=8,
                 port=1,
                 port_out=2,
                 data_path=self.db_path,
                 ignore_all_checks=True)
        a.dump_yaml(self.dump_path)
        a.close()
        with open(self.dump_path) as fp:
            content_a = fp.readlines()
        b = GNES.load_yaml(self.dump_path)
        b.dump_yaml(self.dump_path)
        b.close()
        with open(self.dump_path) as fp:
            content_b = fp.readlines()
        self.assertEqual(content_a, content_b)

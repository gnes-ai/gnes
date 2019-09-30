import unittest

from gnes.flow import Flow, Service as gfs


class TestGNESFlow(unittest.TestCase):

    def test_flow1(self):
        f = (Flow(check_version=False, route_table=True)
             .add(gfs.Router, yaml_path='BaseRouter').build())
        print(f._service_edges)
        print(f.to_mermaid())

    def test_flow2(self):
        f = (Flow(check_version=False, route_table=True)
             .add(gfs.Router, yaml_path='BaseRouter')
             .add(gfs.Router, yaml_path='BaseRouter')
             .add(gfs.Router, yaml_path='BaseRouter')
             .add(gfs.Router, yaml_path='BaseRouter')
             .add(gfs.Router, yaml_path='BaseRouter')
             .add(gfs.Router, yaml_path='BaseRouter')
             .add(gfs.Router, yaml_path='BaseRouter')
             .add(gfs.Router, yaml_path='BaseRouter')
             .build())
        print(f._service_edges)
        print(f.to_mermaid())

    def test_flow3(self):
        f = (Flow(check_version=False, route_table=True)
             .add(gfs.Router, name='r0', service_out=gfs.Frontend, yaml_path='BaseRouter')
             .add(gfs.Router, name='r1', service_in=gfs.Frontend, yaml_path='BaseRouter')
             .build())
        print(f._service_edges)
        print(f.to_mermaid())

    def test_flow4(self):
        f = (Flow(check_version=False, route_table=True)
             .add(gfs.Router, name='r0', yaml_path='BaseRouter')
             .add(gfs.Router, name='r1', service_in=gfs.Frontend, yaml_path='BaseRouter')
             .add(gfs.Router, name='reduce', service_in=['r0', 'r1'], yaml_path='BaseRouter')
             .build())
        print(f._service_edges)
        print(f.to_mermaid())

    def test_flow5(self):
        f = (Flow(check_version=False, route_table=True)
             .add(gfs.Preprocessor, name='prep', yaml_path='SentSplitPreprocessor')
             .add(gfs.Encoder, yaml_path='PyTorchTransformers')
             .add(gfs.Indexer, name='vec_idx', yaml_path='NumpyIndexer')
             .add(gfs.Indexer, name='doc_idx', yaml_path='DictIndexer', service_in='prep')
             .add(gfs.Router, name='sync_barrier', yaml_path='BaseReduceRouter',
                  num_part=2, service_in=['vec_idx', 'doc_idx'])
             .build())
        print(f._service_edges)
        print(f.to_mermaid())

import os
import unittest

from gnes.cli.parser import set_client_cli_parser
from gnes.flow import Flow, Service as gfs


class TestGNESFlow(unittest.TestCase):

    def setUp(self):
        self.dirname = os.path.dirname(__file__)
        self.test_file = os.path.join(self.dirname, 'sonnets_small.txt')
        self.index_args = set_client_cli_parser().parse_args([
            '--mode', 'index',
            '--txt_file', self.test_file,
            '--batch_size', '4'
        ])
        os.unsetenv('http_proxy')
        os.unsetenv('https_proxy')

    def test_flow1(self):
        f = (Flow(check_version=False, route_table=True)
             .add(gfs.Router, yaml_path='BaseRouter').build())
        print(f._service_edges)
        print(f.to_mermaid())

    def test_flow1_ctx_empty(self):
        f = (Flow(check_version=False, route_table=True)
             .add(gfs.Router, yaml_path='BaseRouter'))
        with f(backend='process'):
            pass

    def test_flow1_ctx(self):
        flow = (Flow(check_version=False, route_table=False)
                .add(gfs.Router, yaml_path='BaseRouter'))
        with flow(backend='process') as f, open(self.test_file) as fp:
            f.index(txt_file=self.test_file, batch_size=4)
            f.index(bytes_gen=(v.encode() for v in fp), batch_size=4)
            f.train(txt_file=self.test_file, batch_size=4)

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
             .build(backend=None))
        print(f._service_edges)
        print(f.to_mermaid())

    def test_flow3(self):
        f = (Flow(check_version=False, route_table=True)
             .add(gfs.Router, name='r0', service_out=gfs.Frontend, yaml_path='BaseRouter')
             .add(gfs.Router, name='r1', service_in=gfs.Frontend, yaml_path='BaseRouter')
             .build(backend=None))
        print(f._service_edges)
        print(f.to_mermaid())

    def test_flow4(self):
        f = (Flow(check_version=False, route_table=True)
             .add(gfs.Router, name='r0', yaml_path='BaseRouter')
             .add(gfs.Router, name='r1', service_in=gfs.Frontend, yaml_path='BaseRouter')
             .add(gfs.Router, name='reduce', service_in=['r0', 'r1'], yaml_path='BaseRouter')
             .build(backend=None))
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
             .build(backend=None))
        print(f._service_edges)
        print(f.to_mermaid())

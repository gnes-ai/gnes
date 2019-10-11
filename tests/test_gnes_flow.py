import os
import unittest

from gnes.cli.parser import set_client_cli_parser
from gnes.flow import Flow, Service as gfs, FlowBuildLevelMismatch, FlowTopologyError


class TestGNESFlow(unittest.TestCase):

    def setUp(self):
        self.dirname = os.path.dirname(__file__)
        self.test_file = os.path.join(self.dirname, 'sonnets_small.txt')
        self.yamldir = os.path.join(self.dirname, 'yaml')
        self.index_args = set_client_cli_parser().parse_args([
            '--mode', 'index',
            '--txt_file', self.test_file,
            '--batch_size', '4'
        ])
        os.unsetenv('http_proxy')
        os.unsetenv('https_proxy')
        self.test_dir = os.path.join(self.dirname, 'test_flow')
        self.indexer1_bin = os.path.join(self.test_dir, 'my_faiss_indexer.bin')
        self.indexer2_bin = os.path.join(self.test_dir, 'my_fulltext_indexer.bin')
        self.encoder_bin = os.path.join(self.test_dir, 'my_transformer.bin')
        if os.path.exists(self.test_dir):
            self.tearDown()
        os.mkdir(self.test_dir)

        os.environ['TEST_WORKDIR'] = self.test_dir

    def tearDown(self):
        for k in [self.indexer1_bin, self.indexer2_bin, self.encoder_bin]:
            if os.path.exists(k):
                os.remove(k)
        os.rmdir(self.test_dir)

    def test_flow1(self):
        f = (Flow(check_version=False, route_table=True)
             .add(gfs.Router, yaml_path='BaseRouter'))
        g = f.add(gfs.Router, yaml_path='BaseRouter')

        print('f: %r g: %r' % (f, g))
        g.build()
        print(g.to_mermaid())

        f = f.add(gfs.Router, yaml_path='BaseRouter')
        g = g.add(gfs.Router, yaml_path='BaseRouter')

        print('f: %r g: %r' % (f, g))
        f.build()
        print(f.to_mermaid())
        self.assertRaises(FlowTopologyError, g.build)

    def test_flow1_ctx_empty(self):
        f = (Flow(check_version=False, route_table=True)
             .add(gfs.Router, yaml_path='BaseRouter'))
        with f(backend='process'):
            pass

    def test_flow1_ctx(self):
        flow = (Flow(check_version=False, route_table=False)
                .add(gfs.Router, yaml_path='BaseRouter'))
        with flow(backend='process', copy_flow=True) as f, open(self.test_file) as fp:
            f.index(txt_file=self.test_file, batch_size=4)
            f.train(txt_file=self.test_file, batch_size=4)

        with flow(backend='process', copy_flow=True) as f:
            # change the flow inside build shall fail
            f = f.add(gfs.Router, yaml_path='BaseRouter')
            self.assertRaises(FlowBuildLevelMismatch, f.index, txt_file=self.test_file, batch_size=4)

        print(flow.build(backend=None).to_mermaid())

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
        f.to_jpg()

    def _test_index_flow(self, backend):
        for k in [self.indexer1_bin, self.indexer2_bin, self.encoder_bin]:
            self.assertFalse(os.path.exists(k))

        flow = (Flow(check_version=False, route_table=False)
                .add(gfs.Preprocessor, name='prep', yaml_path='SentSplitPreprocessor')
                .add(gfs.Encoder, yaml_path=os.path.join(self.dirname, 'yaml/flow-transformer.yml'))
                .add(gfs.Indexer, name='vec_idx', yaml_path=os.path.join(self.dirname, 'yaml/flow-vecindex.yml'))
                .add(gfs.Indexer, name='doc_idx', yaml_path=os.path.join(self.dirname, 'yaml/flow-dictindex.yml'),
                     service_in='prep')
                .add(gfs.Router, name='sync_barrier', yaml_path='BaseReduceRouter',
                     num_part=2, service_in=['vec_idx', 'doc_idx']))

        with flow.build(backend=backend) as f:
            f.index(txt_file=self.test_file, batch_size=20)

        for k in [self.indexer1_bin, self.indexer2_bin]:
            self.assertTrue(os.path.exists(k))

    def _test_query_flow(self, backend):
        flow = (Flow(check_version=False, route_table=False)
                .add(gfs.Preprocessor, name='prep', yaml_path='SentSplitPreprocessor')
                .add(gfs.Encoder, yaml_path=os.path.join(self.dirname, 'yaml/flow-transformer.yml'))
                .add(gfs.Indexer, name='vec_idx', yaml_path=os.path.join(self.dirname, 'yaml/flow-vecindex.yml'))
                .add(gfs.Router, name='scorer', yaml_path=os.path.join(self.dirname, 'yaml/flow-score.yml'))
                .add(gfs.Indexer, name='doc_idx', yaml_path=os.path.join(self.dirname, 'yaml/flow-dictindex.yml')))

        with flow.build(backend=backend) as f, open(self.test_file, encoding='utf8') as fp:
            f.query(bytes_gen=[v.encode() for v in fp][:3])

    # @unittest.SkipTest
    def test_index_query_flow(self):
        self._test_index_flow('thread')
        self._test_query_flow('thread')

    def test_indexe_query_flow_proc(self):
        self._test_index_flow('process')
        self._test_query_flow('process')

import os
import unittest

from gnes.cli.parser import set_client_cli_parser
from gnes.flow import Flow, FlowBuildLevelMismatch
from gnes.flow.base import BaseIndexFlow, BaseQueryFlow


class TestGNESFlow(unittest.TestCase):

    def setUp(self):
        self.dirname = os.path.dirname(__file__)
        self.test_file = os.path.join(self.dirname, 'sonnets_small.txt')
        self.yamldir = os.path.join(self.dirname, 'yaml')
        self.dump_flow_path = os.path.join(self.dirname, 'test-flow.bin')
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
        for k in [self.indexer1_bin, self.indexer2_bin, self.encoder_bin, self.dump_flow_path]:
            if os.path.exists(k):
                os.remove(k)
        os.rmdir(self.test_dir)

    def test_flow1(self):
        f = (Flow(check_version=False, route_table=True)
             .add_router(yaml_path='BaseRouter'))
        g = f.add_router(yaml_path='BaseRouter')

        print('f: %r g: %r' % (f, g))
        g.build()
        print(g.to_mermaid())

        f = f.add_router(yaml_path='BaseRouter')
        g = g.add_router(yaml_path='BaseRouter')

        print('f: %r g: %r' % (f, g))
        f.build()
        print(f.to_mermaid())
        g.build()

    def test_flow1_ctx_empty(self):
        f = (Flow(check_version=False, route_table=True)
             .add_router(yaml_path='BaseRouter'))
        with f(backend='process'):
            pass

    def test_flow1_ctx(self):
        flow = (Flow(check_version=False, route_table=False)
                .add_router(yaml_path='BaseRouter'))
        with flow(backend='process', copy_flow=True) as f, open(self.test_file) as fp:
            f.index(txt_file=self.test_file, batch_size=4)
            f.train(txt_file=self.test_file, batch_size=4)

        with flow(backend='process', copy_flow=True) as f:
            # change the flow inside build shall fail
            f = f.add_router(yaml_path='BaseRouter')
            self.assertRaises(FlowBuildLevelMismatch, f.index, txt_file=self.test_file, batch_size=4)

        print(flow.build(backend=None).to_mermaid())

    def test_flow2(self):
        f = (Flow(check_version=False, route_table=True)
             .add_router(yaml_path='BaseRouter')
             .add_router(yaml_path='BaseRouter')
             .add_router(yaml_path='BaseRouter')
             .add_router(yaml_path='BaseRouter')
             .add_router(yaml_path='BaseRouter')
             .add_router(yaml_path='BaseRouter')
             .add_router(yaml_path='BaseRouter')
             .add_router(yaml_path='BaseRouter')
             .build(backend=None))
        print(f._service_edges)
        print(f.to_mermaid())

    def test_flow3(self):
        f = (Flow(check_version=False, route_table=True)
             .add_router(name='r0', send_to=Flow.Frontend, yaml_path='BaseRouter')
             .add_router(name='r1', recv_from=Flow.Frontend, yaml_path='BaseRouter')
             .build(backend=None))
        print(f._service_edges)
        print(f.to_mermaid())

    def test_flow4(self):
        f = (Flow(check_version=False, route_table=True)
             .add_router(name='r0', yaml_path='BaseRouter')
             .add_router(name='r1', recv_from=Flow.Frontend, yaml_path='BaseRouter')
             .add_router(name='reduce', recv_from=['r0', 'r1'], yaml_path='BaseRouter')
             .build(backend=None))
        print(f._service_edges)
        print(f.to_mermaid())

    def test_flow5(self):
        f = (Flow(check_version=False, route_table=True)
             .add_preprocessor(name='prep', yaml_path='SentSplitPreprocessor')
             .add_encoder(yaml_path='PyTorchTransformers')
             .add_indexer(name='vec_idx', yaml_path='NumpyIndexer')
             .add_indexer(name='doc_idx', yaml_path='DictIndexer', recv_from='prep')
             .add_router(name='sync_barrier', yaml_path='BaseReduceRouter',
                         num_part=2, recv_from=['vec_idx', 'doc_idx'])
             .build(backend=None))
        print(f._service_edges)
        print(f.to_mermaid())
        # f.to_jpg()

    def test_flow_replica_pot(self):
        f = (Flow(check_version=False, route_table=True)
             .add_preprocessor(name='prep', yaml_path='SentSplitPreprocessor', replicas=4)
             .add_encoder(yaml_path='PyTorchTransformers', replicas=3)
             .add_indexer(name='vec_idx', yaml_path='NumpyIndexer', replicas=2)
             .add_indexer(name='doc_idx', yaml_path='DictIndexer', recv_from='prep', replicas=2)
             .add_router(name='sync_barrier', yaml_path='BaseReduceRouter',
                         num_part=2, recv_from=['vec_idx', 'doc_idx'])
             .build(backend=None))
        print(f.to_mermaid())
        print(f.to_url(left_right=False))
        print(f.to_url(left_right=True))

    def _test_index_flow(self, backend):
        for k in [self.indexer1_bin, self.indexer2_bin, self.encoder_bin]:
            self.assertFalse(os.path.exists(k))

        flow = (Flow(check_version=False, route_table=False)
                .add_preprocessor(name='prep', yaml_path='SentSplitPreprocessor')
                .add_encoder(yaml_path=os.path.join(self.dirname, 'yaml/flow-transformer.yml'), replicas=3)
                .add_indexer(name='vec_idx', yaml_path=os.path.join(self.dirname, 'yaml/flow-vecindex.yml'))
                .add_indexer(name='doc_idx', yaml_path=os.path.join(self.dirname, 'yaml/flow-dictindex.yml'),
                             recv_from='prep')
                .add_router(name='sync_barrier', yaml_path='BaseReduceRouter',
                            num_part=2, recv_from=['vec_idx', 'doc_idx']))

        with flow.build(backend=backend) as f:
            f.index(txt_file=self.test_file, batch_size=20)

        for k in [self.indexer1_bin, self.indexer2_bin]:
            self.assertTrue(os.path.exists(k))

    def _test_query_flow(self, backend):
        flow = (Flow(check_version=False, route_table=False)
                .add_preprocessor(name='prep', yaml_path='SentSplitPreprocessor')
                .add_encoder(yaml_path=os.path.join(self.dirname, 'yaml/flow-transformer.yml'), replicas=3)
                .add_indexer(name='vec_idx', yaml_path=os.path.join(self.dirname, 'yaml/flow-vecindex.yml'))
                .add_router(name='scorer', yaml_path=os.path.join(self.dirname, 'yaml/flow-score.yml'))
                .add_indexer(name='doc_idx', yaml_path=os.path.join(self.dirname, 'yaml/flow-dictindex.yml')))

        with flow.build(backend=backend) as f, open(self.test_file, encoding='utf8') as fp:
            f.query(bytes_gen=[v.encode() for v in fp][:3])

    # @unittest.SkipTest
    def test_index_query_flow(self):
        self._test_index_flow('thread')
        self._test_query_flow('thread')

    def test_indexe_query_flow_proc(self):
        self._test_index_flow('process')
        self._test_query_flow('process')

    def test_query_flow_plot(self):
        flow = (Flow(check_version=False, route_table=False)
                .add_preprocessor(name='prep', yaml_path='SentSplitPreprocessor', replicas=2)
                .add_encoder(yaml_path=os.path.join(self.dirname, 'yaml/flow-transformer.yml'), replicas=3)
                .add_indexer(name='vec_idx', yaml_path=os.path.join(self.dirname, 'yaml/flow-vecindex.yml'),
                             replicas=4)
                .add_router(name='scorer', yaml_path=os.path.join(self.dirname, 'yaml/flow-score.yml'))
                .add_indexer(name='doc_idx', yaml_path=os.path.join(self.dirname, 'yaml/flow-dictindex.yml')))
        print(flow.build(backend=None).to_url())

    def test_flow_add_set(self):
        f = (Flow(check_version=False, route_table=True)
             .add_preprocessor(name='prep', yaml_path='SentSplitPreprocessor', replicas=4)
             .add_encoder(yaml_path='PyTorchTransformers', replicas=3)
             .add_indexer(name='vec_idx', yaml_path='NumpyIndexer', replicas=2)
             .add_indexer(name='doc_idx', yaml_path='DictIndexer', recv_from='prep', replicas=2)
             .add_router(name='sync_barrier', yaml_path='BaseReduceRouter',
                         num_part=2, recv_from=['vec_idx', 'doc_idx'])
             .build(backend=None))

        print(f.to_url())
        print(f.set('prep', replicas=1).build(backend=None).to_url())
        # make it as query flow

        f1 = (f
              .remove('sync_barrier')
              .remove('doc_idx')
              .set_last_service('vec_idx')
              .add_router('scorer', yaml_path=os.path.join(self.dirname, 'yaml/flow-score.yml'))
              .add_indexer('doc_idx', yaml_path='DictIndexer', replicas=2)
              .build(backend=None))

        print(f1.to_url())

        # another way to convert f to an index flow

        f2 = (f
              .set_last_service('vec_idx')
              .add_router('scorer', yaml_path=os.path.join(self.dirname, 'yaml/flow-score.yml'))
              .set('doc_idx', recv_from='scorer', yaml_path='DictIndexer', replicas=2, clear_old_attr=True)
              .remove('sync_barrier')
              .set_last_service('doc_idx')
              .build(backend=None))

        print(f2.to_url())

        self.assertEqual(f1, f2)

        self.assertNotEqual(f1, f2.add_router('dummy', yaml_path='BaseRouter'))

        print(f1.to_python_code())
        print(f.to_python_code())

        f1.dump(self.dump_flow_path)
        f3 = Flow.load(self.dump_flow_path)
        self.assertEqual(f1, f3)

        print(f1.to_swarm_yaml())

    def test_common_flow(self):
        print(BaseIndexFlow().build(backend=None).to_url())
        print(BaseQueryFlow().build(backend=None).to_url())

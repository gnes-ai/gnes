import copy
import random
from typing import Dict, List

import pkg_resources
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from ..helper import set_logger
from ..service.base import SocketType

_yaml = YAML()


class YamlGraph:
    comp2file = {
        'Encoder': 'service.encoder.EncoderService',
        'Router': 'service.router.RouterService',
        'Indexer': 'service.indexer.IndexerService',
        'Frontend': 'service.grpc.GRPCFrontend',
        'Preprocessor': 'service.preprocessor.PreprocessorService'
    }

    class Layer:
        default_values = {
            'name': None,
            'yaml_path': None,
            'dump_path': None,
            'replicas': 1,
            'income': 'pull'
        }

        def __init__(self, id: int = 0):
            self.id = id
            self.components = []

        @staticmethod
        def get_value(comp: Dict, key: str):
            return comp.get(key, YamlGraph.Layer.default_values[key])

        @property
        def is_homogenous(self):
            return len(self.components) == 1

        @property
        def is_single_component(self):
            return self.is_homogenous and self.get_value(self.components[0], 'replicas') == 1

        @property
        def is_homo_multi_component(self):
            return self.is_homogenous and not self.is_single_component

        @property
        def is_heto_single_component(self):
            return not self.is_homogenous and all(self.get_value(c, 'replicas') == 1 for c in self.components)

        @property
        def get_component_name(self, unique: bool = False):
            r = [c['name'] for c in self.components]
            if unique:
                r = list(set(r))
            return r

        def append(self, comp):
            self.components.append(comp)

        def __repr__(self):
            return str(self.components)

    def __init__(self, args):

        self._layers = []  # type: List['YamlGraph.Layer']
        self.logger = set_logger(self.__class__.__name__)
        tmp = _yaml.load(args.yaml_path)
        self.name = tmp.get('name', args.name)
        self.port = tmp.get('port', args.port)
        self.args = args
        self._num_layer = 0

        if 'component' in tmp:
            self.add_layer()
            self.add_comp(CommentedMap({'name': 'Frontend'}))
            for comp in tmp['component']:
                self.add_layer()
                if isinstance(comp, list):
                    [self.add_comp(c) for c in comp if self.add_comp(c)]
                elif self.check_fields(comp):
                    self.add_comp(comp)
                else:
                    raise ValueError(comp)
        else:
            self.logger.error('yaml file defines an empty graph! no "component" field exists!')

    def check_fields(self, comp: Dict) -> bool:
        if 'name' not in comp:
            raise AttributeError('a component must have a name (choices: %s)' % ', '.join(self.comp2file.keys()))
        if comp['name'] not in self.comp2file:
            raise AttributeError(
                'a component must be one of: %s, but given %s' % (', '.join(self.comp2file.keys()), comp['name']))
        if 'yaml_path' not in comp and 'dump_path' not in comp:
            self.logger.warning(
                'you did not specify "yaml_path" and "dump_path", '
                'will use a default config and would probably result in an empty model')
        for k in comp:
            if k not in self.Layer.default_values:
                self.logger.warning('your yaml contains an unrecognized key named "%s"' % k)
        return True

    def add_layer(self, layer: 'Layer' = None) -> None:
        self._layers.append(copy.deepcopy(layer) or self.Layer(id=self._num_layer))
        self._num_layer += 1

    def add_comp(self, comp: Dict) -> None:
        self._layers[-1].append(comp)

    def build_layers(self) -> List['YamlGraph.Layer']:
        all_layers = []  # type: List['YamlGraph.Layer']
        for idx, layer in enumerate(self._layers[1:] + [self._layers[0]], 1):
            last_layer = self._layers[idx - 1]
            for l in self._add_router(last_layer, layer):
                all_layers.append(copy.deepcopy(l))
        # # add frontend
        # for l in self._add_router(all_layers[-1], all_layers[0]):
        #     all_layers.append(copy.deepcopy(l))
        all_layers[0] = copy.deepcopy(self._layers[0])
        return all_layers

    @staticmethod
    def build_mermaid(all_layers: List['YamlGraph.Layer'], show_topdown: bool = True):
        mermaid_graph = []
        for l_idx, layer in enumerate(all_layers[1:] + [all_layers[0]], 1):
            last_layer = all_layers[l_idx - 1]

            for c_idx, c in enumerate(last_layer.components):
                # if len(last_layer.components) > 1:
                #     self.mermaid_graph.append('\tsubgraph %s%d' % (c['name'], c_idx))
                for j in range(YamlGraph.Layer.get_value(c, 'replicas')):
                    for c1_idx, c1 in enumerate(layer.components):
                        if c1['port_in'] == c['port_out']:
                            p = '((%s%s))' if c['name'] == 'Router' else '[%s%s]'
                            p1 = '((%s%s))' if c1['name'] == 'Router' else '[%s%s]'
                            for j1 in range(YamlGraph.Layer.get_value(c1, 'replicas')):
                                id, id1 = '%s%s%s' % (last_layer.id, c_idx, j), '%s%s%s' % (layer.id, c1_idx, j1)
                                conn_type = (
                                        c['socket_out'].split('_')[0] + '/' + c1['socket_in'].split('_')[0]).lower()
                                s_id = '%s%s' % (c_idx if len(last_layer.components) > 1 else '',
                                                 j if YamlGraph.Layer.get_value(c, 'replicas') > 1 else '')
                                s1_id = '%s%s' % (c1_idx if len(layer.components) > 1 else '',
                                                  j1 if YamlGraph.Layer.get_value(c1, 'replicas') > 1 else '')
                                mermaid_graph.append(
                                    '\t%s%s%s-- %s -->%s%s%s' % (
                                        c['name'], id, p % (c['name'], s_id), conn_type, c1['name'], id1,
                                        p1 % (c1['name'], s1_id)))
                # if len(last_layer.components) > 1:
                #     self.mermaid_graph.append('\tend')

        style = 'style Frontend000 fill:#ffd889ff,stroke:#f66,stroke-width:2px,stroke-dasharray:5'
        mermaid_str = '\n'.join(['graph TD' if show_topdown else 'graph LR'] + [style] + mermaid_graph)
        return mermaid_str

    def build_html(self, mermaid_str: str):
        if not self.args.html_path:
            print(mermaid_str)
        else:
            r = pkg_resources.resource_stream('gnes', '/'.join(('resources', 'static', 'gnes-graph.html')))
            with r, self.args.html_path as fp:
                html = r.read().decode().replace('@mermaid-graph', mermaid_str)
                fp.write(html)

    @staticmethod
    def _get_random_port(min_port: int = 49152, max_port: int = 65536) -> str:
        return str(random.randrange(min_port, max_port))

    def _add_router(self, last_layer: 'YamlGraph.Layer', layer: 'YamlGraph.Layer') -> List['YamlGraph.Layer']:
        def rule1():
            # a shortcut fn: push connect the last and current
            last_layer.components[0]['socket_out'] = str(SocketType.PUSH_BIND)
            layer.components[0]['socket_in'] = str(SocketType.PULL_CONNECT)

        def rule2():
            # a shortcut fn: pub connect the last and the current
            last_layer.components[0]['socket_out'] = str(SocketType.PUB_BIND)
            layer.components[0]['socket_in'] = str(SocketType.SUB_CONNECT)

        def rule3():
            # a shortcut fn: (N)-2-(N) with push pull connection
            router_layer = YamlGraph.Layer(id=self._num_layer)
            self._num_layer += 1
            last_layer.components[0]['socket_out'] = str(SocketType.PUSH_CONNECT)
            r = CommentedMap({'name': 'Router',
                              'yaml_path': None,
                              'socket_in': str(SocketType.PULL_BIND),
                              'socket_out': str(SocketType.PUSH_BIND),
                              'port_in': last_layer.components[0]['port_out'],
                              'port_out': self._get_random_port()})
            layer.components[0]['socket_in'] = str(SocketType.PULL_CONNECT)
            layer.components[0]['port_in'] = r['port_out']
            router_layer.append(r)
            router_layers.append(router_layer)

        def rule4():
            # a shortcut fn: (N)-to-(1)&(1)&(1)
            last_layer.components[0]['socket_out'] = str(SocketType.PUB_BIND)
            for c in layer.components:
                c['socket_in'] = str(SocketType.SUB_CONNECT)

        def rule5():
            # a shortcut fn: based on c3(): (N)-2-(N) with pub sub connection
            rule3()
            router_layers[0].components[0]['socket_out'] = str(SocketType.PUB_BIND)
            for c in layer.components:
                c['socket_in'] = str(SocketType.SUB_CONNECT)

        def rule6():
            last_layer.components[0]['socket_out'] = str(SocketType.PUB_BIND)
            router_layer = YamlGraph.Layer(id=self._num_layer)
            self._num_layer += 1
            for c in layer.components:
                r = CommentedMap({'name': 'Router',
                                  'yaml_path': None,
                                  'socket_in': str(SocketType.SUB_CONNECT),
                                  'socket_out': str(SocketType.PUSH_BIND),
                                  'port_in': last_layer.components[0]['port_out'],
                                  'port_out': self._get_random_port()})
                c['socket_in'] = str(SocketType.PULL_CONNECT)
                c['port_in'] = r['port_out']
                router_layer.append(r)
            router_layers.append(router_layer)

        def rule7():
            last_layer.components[0]['socket_out'] = str(SocketType.PUSH_CONNECT)

            router_layer = YamlGraph.Layer(id=self._num_layer)
            self._num_layer += 1
            r0 = CommentedMap({'name': 'Router',
                               'yaml_path': None,
                               'socket_in': str(SocketType.PULL_BIND),
                               'socket_out': str(SocketType.PUB_BIND),
                               'port_in': self._get_random_port(),
                               'port_out': self._get_random_port()})
            router_layer.append(r0)
            router_layers.append(router_layer)
            last_layer.components[0]['port_out'] = r0['port_in']

            router_layer = YamlGraph.Layer(id=self._num_layer)
            self._num_layer += 1
            for c in layer.components:
                r = CommentedMap({'name': 'Router',
                                  'yaml_path': None,
                                  'socket_in': str(SocketType.SUB_CONNECT),
                                  'socket_out': str(SocketType.PUSH_BIND),
                                  'port_in': r0['port_out'],
                                  'port_out': self._get_random_port()})
                c['socket_in'] = str(SocketType.PULL_CONNECT)
                c['port_in'] = r['port_out']
                router_layer.append(r)
            router_layers.append(router_layer)

        def rule8():
            last_layer.components[0]['socket_out'] = str(SocketType.PUSH_CONNECT)
            router_layer = YamlGraph.Layer(id=self._num_layer)
            self._num_layer += 1
            r = CommentedMap({'name': 'Router',
                              'yaml_path': None,
                              'socket_in': str(SocketType.PULL_BIND),
                              'socket_out': str(SocketType.PUSH_BIND),
                              'port_in': self._get_random_port(),
                              'port_out': self._get_random_port()})
            router_layer.append(r)

            for c in last_layer.components:
                c['socket_out'] = str(SocketType.PUSH_CONNECT)
                c['port_out'] = self._get_random_port()
                r_c = CommentedMap({'name': 'Router',
                                    'yaml_path': None,
                                    'socket_in': str(SocketType.PULL_BIND),
                                    'socket_out': str(SocketType.PUSH_BIND),
                                    'port_in': c['port_out'],
                                    'port_out': r['port_in']})
                router_layer.append(r_c)

            for c in layer.components:
                c['socket_in'] = str(SocketType.PULL_CONNECT)
                c['port_in'] = r['port_out']
            router_layers.append(router_layer)

            router_layer = YamlGraph.Layer(id=self._num_layer)
            self._num_layer += 1
            router_layer.append(r)
            router_layers.append(router_layer)

        def rule9():
            # a shortcut fn: push connect the last and current
            last_layer.components[0]['socket_out'] = str(SocketType.PUSH_CONNECT)
            layer.components[0]['socket_in'] = str(SocketType.PULL_BIND)

        router_layers = []  # type: List['self.Layer']
        # bind the last out to current in
        last_layer.components[0]['port_out'] = self._get_random_port()
        layer.components[0]['port_in'] = last_layer.components[0]['port_out']
        if last_layer.is_single_component:
            # 1-to-?
            if layer.is_single_component:
                # 1-to-(1)
                # no router is needed
                rule1()
            elif layer.is_homo_multi_component:
                # 1-to-(N)
                last_income = self.Layer.get_value(last_layer.components[0], 'income')
                if last_income == 'pull':
                    rule1()
                elif last_income == 'sub':
                    rule2()
                else:
                    raise NotImplementedError('replica type: %s is not recognized!' % last_income)
            elif layer.is_heto_single_component:
                # 1-to-(1)&(1)&(1)
                rule4()
            else:
                # 1-to-(N)&(N)&(N)
                rule6()
        elif last_layer.is_homo_multi_component:
            # (N)-to-?
            last_income = self.Layer.get_value(last_layer.components[0], 'income')

            if layer.is_single_component:
                if last_income == 'pull':
                    # (N)-to-1
                    rule9()
                elif last_income == 'sub':
                    # (N)-to-1 with a sync barrier
                    rule3()
                else:
                    raise NotImplementedError('replica type: %s is not recognized!' % last_income)
            elif layer.is_homo_multi_component:
                # (N)-to-(N)
                # need a router anyway
                if self.Layer.get_value(layer.components[0], 'income') == 'sub':
                    rule5()
                else:
                    rule3()
            elif layer.is_heto_single_component:
                # (N)-to-(1)&(1)&(1)
                rule5()
            else:
                rule7()
        elif last_layer.is_heto_single_component:
            rule3()
        else:
            rule8()
        return [last_layer, *router_layers]

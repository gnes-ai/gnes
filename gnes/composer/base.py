import copy
import random
import time
from collections import defaultdict
from typing import Dict, List

import pkg_resources
from ruamel.yaml import YAML, StringIO
from ruamel.yaml.comments import CommentedMap
from termcolor import colored

from .. import __version__
from ..helper import set_logger
from ..service.base import SocketType

_yaml = YAML()


class YamlGraph:
    comp2file = {
        'Encoder': 'encode',
        'Router': 'route',
        'Indexer': 'index',
        'Frontend': 'frontend',
        'Preprocessor': 'preprocess'
    }

    class Layer:
        default_values = {
            'name': None,
            'yaml_path': None,
            'dump_path': None,
            'replicas': 1,
            'income': 'pull'
        }

        def __init__(self, layer_id: int = 0):
            self.layer_id = layer_id
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
        with args.yaml_path:
            tmp = _yaml.load(args.yaml_path)
            stream = StringIO()
            _yaml.dump(tmp, stream)
        self.original_yaml = stream.getvalue()
        self.name = tmp.get('name', args.name)
        self.port = tmp.get('port', args.port)
        self.args = args
        self._num_layer = 0

        if 'services' in tmp:
            self.add_layer()
            self.add_comp(CommentedMap({'name': 'Frontend', 'grpc_port': self.port}))
            for comp in tmp['services']:
                self.add_layer()
                if isinstance(comp, list):
                    for c in comp:
                        self.add_comp(c)
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
                'found empty "yaml_path" and "dump_path", '
                'i will use a default config and would probably result in an empty model')
        for k in comp:
            if k not in self.Layer.default_values:
                self.logger.warning('your yaml contains an unrecognized key named "%s"' % k)
        return True

    def add_layer(self, layer: 'Layer' = None) -> None:
        self._layers.append(copy.deepcopy(layer) or self.Layer(layer_id=self._num_layer))
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
    def build_dockerswarm(all_layers: List['YamlGraph.Layer'], docker_img: str = 'gnes/gnes:latest',
                          volumes: Dict = None) -> str:
        swarm_lines = {'version': '3.4', 'services': {}}
        taboo = {'name', 'replicas', 'yaml_path', 'dump_path'}
        config_dict = {}
        network_dict = {'gnes-network': {'driver': 'overlay', 'attachable': True}}
        for l_idx, layer in enumerate(all_layers):
            for c_idx, c in enumerate(layer.components):
                c_name = '%s%d%d' % (c['name'], l_idx, c_idx)
                args = ['--%s %s' % (a, str(v) if ' ' not in str(v) else ('"%s"' % str(v))) for a, v in c.items() if
                        a not in taboo and v]
                if 'yaml_path' in c and c['yaml_path'] is not None:
                    args.append('--yaml_path /%s_yaml' % c_name)
                    config_dict['%s_yaml' % c_name] = {'file': c['yaml_path']}

                if l_idx + 1 < len(all_layers):
                    next_layer = all_layers[l_idx + 1]
                    _l_idx = l_idx + 1
                else:
                    next_layer = all_layers[0]
                    _l_idx = 0

                host_out_name = ''
                for _c_idx, _c in enumerate(next_layer.components):
                    if _c['port_in'] == c['port_out']:
                        host_out_name = '%s%d%d' % (_c['name'], _l_idx, _c_idx)
                        break

                if l_idx - 1 >= 0:
                    last_layer = all_layers[l_idx - 1]
                    _l_idx = l_idx - 1
                else:
                    last_layer = all_layers[-1]
                    _l_idx = len(all_layers) - 1

                host_in_name = ''
                for _c_idx, _c in enumerate(last_layer.components):
                    if _c['port_out'] == c['port_in']:
                        host_in_name = '%s%d%d' % (_c['name'], _l_idx, _c_idx)
                        break

                args += ['--host_in %s' % host_in_name]
                         # '--host_out %s' % host_out_name]

                cmd = '%s %s' % (YamlGraph.comp2file[c['name']], ' '.join(args))
                swarm_lines['services'][c_name] = {
                    'image': docker_img,
                    'command': cmd,
                }

                rep_c = YamlGraph.Layer.get_value(c, 'replicas')
                if rep_c > 1:
                    swarm_lines['services'][c_name]['deploy'] = {
                        'replicas': YamlGraph.Layer.get_value(c, 'replicas'),
                        'restart_policy': {
                            'condition': 'on-failure',
                            'max_attempts': 3,
                        }
                    }

                if 'yaml_path' in c and c['yaml_path'] is not None:
                    swarm_lines['services'][c_name]['configs'] = ['%s_yaml' % c_name]

                if c['name'] == 'Frontend':
                    swarm_lines['services'][c_name]['ports'] = ['%d:%d' % (c['grpc_port'], c['grpc_port'])]

        if volumes:
            swarm_lines['volumes'] = volumes
        swarm_lines['configs'] = config_dict
        swarm_lines['networks'] = network_dict
        stream = StringIO()
        _yaml.dump(swarm_lines, stream)
        return stream.getvalue()

    @staticmethod
    def build_kubernetes(all_layers: List['YamlGraph.Layer'], *args, **kwargs):
        pass

    @staticmethod
    def build_shell(all_layers: List['YamlGraph.Layer'], log_redirect: str = None) -> str:
        shell_lines = []
        taboo = {'name', 'replicas'}
        for layer in all_layers:
            for c in layer.components:
                rep_c = YamlGraph.Layer.get_value(c, 'replicas')
                shell_lines.append('printf "starting service %s with %s replicas...\\n"' % (
                    colored(c['name'], 'green'), colored(rep_c, 'yellow')))
                for _ in range(rep_c):
                    cmd = YamlGraph.comp2file[c['name']]
                    args = ' '.join(
                        ['--%s %s' % (a, str(v) if ' ' not in str(v) else ('"%s"' % str(v))) for a, v in c.items() if
                         a not in taboo and v])
                    shell_lines.append('gnes %s %s %s &' % (
                        cmd, args, '>> %s 2>&1' % log_redirect if log_redirect else ''))

        r = pkg_resources.resource_stream('gnes', '/'.join(('resources', 'compose', 'gnes-shell.sh')))
        with r:
            return r.read().decode().replace('{{gnes-template}}', '\n'.join(shell_lines))

    @staticmethod
    def build_mermaid(all_layers: List['YamlGraph.Layer'], mermaid_leftright: bool = False) -> str:
        mermaid_graph = []
        cls_dict = defaultdict(set)
        for l_idx, layer in enumerate(all_layers[1:] + [all_layers[0]], 1):
            last_layer = all_layers[l_idx - 1]

            for c_idx, c in enumerate(last_layer.components):
                # if len(last_layer.components) > 1:
                #     self.mermaid_graph.append('\tsubgraph %s%d' % (c['name'], c_idx))
                for j in range(YamlGraph.Layer.get_value(c, 'replicas')):
                    for c1_idx, c1 in enumerate(layer.components):
                        if c1['port_in'] == c['port_out']:
                            p = '((%s%s))' if c['name'] == 'Router' else '(%s%s)'
                            p1 = '((%s%s))' if c1['name'] == 'Router' else '(%s%s)'
                            for j1 in range(YamlGraph.Layer.get_value(c1, 'replicas')):
                                _id, _id1 = '%s%s%s' % (last_layer.layer_id, c_idx, j), '%s%s%s' % (
                                    layer.layer_id, c1_idx, j1)
                                conn_type = (
                                        c['socket_out'].split('_')[0] + '/' + c1['socket_in'].split('_')[0]).lower()
                                s_id = '%s%s' % (c_idx if len(last_layer.components) > 1 else '',
                                                 j if YamlGraph.Layer.get_value(c, 'replicas') > 1 else '')
                                s1_id = '%s%s' % (c1_idx if len(layer.components) > 1 else '',
                                                  j1 if YamlGraph.Layer.get_value(c1, 'replicas') > 1 else '')
                                mermaid_graph.append(
                                    '\t%s%s%s-- %s -->%s%s%s' % (
                                        c['name'], _id, p % (c['name'], s_id), conn_type, c1['name'], _id1,
                                        p1 % (c1['name'], s1_id)))
                                cls_dict[c['name'] + 'CLS'].add('%s%s' % (c['name'], _id))
                                cls_dict[c1['name'] + 'CLS'].add('%s%s' % (c1['name'], _id1))
                # if len(last_layer.components) > 1:
                #     self.mermaid_graph.append('\tend')

        style = ['classDef FrontendCLS fill:#ffb347,stroke:#277CE8,stroke-width:1px,stroke-dasharray:5;',
                 'classDef EncoderCLS fill:#27E1E8,stroke:#277CE8,stroke-width:1px;',
                 'classDef IndexerCLS fill:#27E1E8,stroke:#277CE8,stroke-width:1px;',
                 'classDef RouterCLS fill:#2BFFCB,stroke:#277CE8,stroke-width:1px;',
                 'classDef PreprocessorCLS fill:#27E1E8,stroke:#277CE8,stroke-width:1px;']
        class_def = ['class %s %s;' % (','.join(v), k) for k, v in cls_dict.items()]
        mermaid_str = '\n'.join(
            ['graph %s' % ('LR' if mermaid_leftright else 'TD')] + mermaid_graph + style + class_def)
        return mermaid_str

    @staticmethod
    def build_html(generate_dict: Dict[str, str]) -> str:
        r = pkg_resources.resource_stream('gnes', '/'.join(('resources', 'static', 'gnes-board.html')))
        with r:
            html = r.read().decode()
            for k, v in generate_dict.items():
                if v:
                    html = html.replace('{{gnes-%s}}' % k, v)
        return html

    def build_all(self):
        def std_or_print(f, content):
            if content:
                if f:
                    with f as fp:
                        fp.write(content)
                        self.logger.info('generated content is written to %s' % f)
                else:
                    self.logger.warning('no file path is defined, i will just print it to stdout')
                    print(content)

        all_layers = self.build_layers()
        cmds = {
            'mermaid': self.build_mermaid(all_layers, self.args.mermaid_leftright),
            'shell': self.build_shell(all_layers, self.args.shell_log_redirect),
            'yaml': self.original_yaml,
            'docker': self.build_dockerswarm(all_layers, self.args.docker_img),
            'k8s': self.build_kubernetes(all_layers),
            'timestamp': time.strftime("%a, %d %b %Y %H:%M:%S"),
            'version': __version__
        }
        std_or_print(self.args.shell_path, cmds['shell'])
        std_or_print(self.args.swarm_path, cmds['docker'])
        std_or_print(self.args.k8s_path, cmds['k8s'])
        std_or_print(self.args.html_path, self.build_html(cmds))

    @staticmethod
    def _get_random_port(min_port: int = 49152, max_port: int = 65536) -> str:
        return str(random.randrange(min_port, max_port))

    @staticmethod
    def _get_random_host(comp_name: str) -> str:
        return str(comp_name + str(random.randrange(0, 100)))

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
            router_layer = YamlGraph.Layer(layer_id=self._num_layer)
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
            router_layer = YamlGraph.Layer(layer_id=self._num_layer)
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

            router_layer = YamlGraph.Layer(layer_id=self._num_layer)
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

            router_layer = YamlGraph.Layer(layer_id=self._num_layer)
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
            router_layer = YamlGraph.Layer(layer_id=self._num_layer)
            self._num_layer += 1
            r = CommentedMap({'name': 'Router',
                              'yaml_path': None,
                              'socket_in': str(SocketType.PULL_BIND),
                              'socket_out': str(SocketType.PUSH_BIND),
                              'port_in': self._get_random_port(),
                              'port_out': self._get_random_port()})

            for c in last_layer.components:
                last_income = self.Layer.get_value(c, 'income')
                if last_income == 'sub':
                    c['socket_out'] = str(SocketType.PUSH_CONNECT)
                    r_c = CommentedMap({'name': 'Router',
                                        'yaml_path': None,
                                        'socket_in': str(SocketType.PULL_BIND),
                                        'socket_out': str(SocketType.PUSH_CONNECT),
                                        'port_in': self._get_random_port(),
                                        'port_out': r['port_in']})
                    c['port_out'] = r_c['port_in']
                    router_layer.append(r_c)
                elif last_income == 'pull':
                    c['socket_out'] = str(SocketType.PUSH_CONNECT)
                    c['port_out'] = r['port_in']

            for c in layer.components:
                c['socket_in'] = str(SocketType.PULL_CONNECT)
                c['port_in'] = r['port_out']

            if router_layer.components:
                router_layers.append(router_layer)
            else:
                self._num_layer -= 1

            router_layer = YamlGraph.Layer(layer_id=self._num_layer)
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

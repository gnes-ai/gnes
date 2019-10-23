import copy
from collections import OrderedDict, defaultdict
from contextlib import ExitStack
from typing import Union, Tuple, List, Optional, Iterator

from .helper import *
from ..base import TrainableBase
from ..helper import set_logger
from ..service.base import SocketType, BaseService


class Flow(TrainableBase):
    """
    GNES Flow: an intuitive way to build workflow for GNES.

    You can use :py:meth:`.add()` then :py:meth:`.build()` to customize your own workflow.
    For example:

    .. highlight:: python
    .. code-block:: python

        from gnes.flow import Flow

        f = (Flow(check_version=False, route_table=True)
             .add_preprocessor(yaml_path='BasePreprocessor')
             .add_encoder(yaml_path='BaseEncoder')
             .add_router(yaml_path='BaseRouter'))

        with f.build(backend='thread') as flow:
            flow.index()
            ...

    You can also use `add('Encoder', ...)` or `add(Service.Encoder, ...)` to add service to the flow.
    The generic :py:meth:`add` provides a convenient way to build the flow.

    As shown above, it is recommend to use flow in the context manner as showed above,
    as it manages all opened sockets/processes/threads automatically when exit from the context.

    Note the different copy behaviors in :py:meth:`.add()` and :py:meth:`.build()`:
    :py:meth:`.add()` always copy the flow by default, whereas :py:meth:`.build()` modify the flow in place.
    You can change this behavior by specifying th argument `copy_flow=False`.

    """

    # a shortcut to the service frontend, removing one extra import
    Frontend = Service.Frontend

    def __init__(self, with_frontend: bool = True, is_trained: bool = True, *args, **kwargs):
        """
        Create a new Flow object.

        :param with_frontend: adding frontend service to the flow
        :param is_trained: indicating whether this flow is trained or not. if set to False then :py:meth:`index`
                            and :py:meth:`query` can not be called before :py:meth:`train`
        :param kwargs: keyword-value arguments that will be shared by all services
        """
        super().__init__(*args, **kwargs)
        self.logger = set_logger(self.__class__.__name__)
        self._service_nodes = OrderedDict()
        self._service_edges = {}
        self._service_name_counter = {k: 0 for k in service_map.keys()}
        self._service_contexts = []
        self._last_changed_service = []
        self._common_kwargs = kwargs
        self._frontend = None
        self._client = None
        self._build_level = BuildLevel.EMPTY
        self._backend = None
        self._init_with_frontend = False
        self.is_trained = is_trained
        if with_frontend:
            self.add_frontend(copy_flow=False)
            self._init_with_frontend = True
        else:
            self.logger.warning('with_frontend is set to False, you need to add_frontend() by yourself')

    @build_required(BuildLevel.GRAPH)
    def to_k8s_yaml(self) -> str:
        raise NotImplementedError

    @build_required(BuildLevel.GRAPH)
    def to_shell_script(self) -> str:
        raise NotImplementedError

    @build_required(BuildLevel.GRAPH)
    def to_swarm_yaml(self, image: str = 'gnes/gnes:latest-alpine') -> str:
        """
        Generate the docker swarm YAML compose file

        :param image: the default GNES docker image
        :return: the generated YAML compose file
        """
        from ruamel.yaml import YAML, StringIO
        _yaml = YAML()
        swarm_yml = {'version': '3.4',
                     'services': {}}

        for k, v in self._service_nodes.items():
            defaults_kwargs, _ = service_map[v['service']]['parser']().parse_known_args(
                ['--yaml_path', 'TrainableBase'])
            non_default_kwargs = {k: v for k, v in vars(v['parsed_args']).items() if getattr(defaults_kwargs, k) != v}
            if not isinstance(non_default_kwargs.get('yaml_path', ''), str):
                non_default_kwargs['yaml_path'] = v['kwargs']['yaml_path']

            num_replicas = None
            if 'num_parallel' in non_default_kwargs:
                num_replicas = non_default_kwargs.pop('num_parallel')

            swarm_yml['services'][k] = {
                'image': v['kwargs'].get('image', image),
                'command': '%s %s' % (
                    service_map[v['service']]['cmd'],
                    ' '.join(['--%s %s' % (k, v) for k, v in non_default_kwargs.items()]))
            }
            if num_replicas and num_replicas > 1:
                swarm_yml['services'][k]['deploy'] = {'replicas': num_replicas}

        stream = StringIO()
        _yaml.dump(swarm_yml, stream)
        return stream.getvalue().strip()

    def to_python_code(self, indent: int = 4) -> str:
        """
        Generate the python code of this flow

        :param indent: the number of whitespaces of indent
        :return: the generated python code
        """
        py_code = ['from gnes.flow import Flow', '']
        kwargs = []
        if not self._init_with_frontend:
            kwargs.append('with_frontend=False')
        if self._common_kwargs:
            kwargs.extend('%s=%s' % (k, v) for k, v in self._common_kwargs.items())
        py_code.append('f = (Flow(%s)' % (', '.join(kwargs)))

        known_service = set()
        last_add_name = ''

        for k, v in self._service_nodes.items():
            kwargs = OrderedDict()
            kwargs['service'] = str(v['service'])
            kwargs['name'] = k
            kwargs['recv_from'] = '[%s]' % (
                ','.join({'\'%s\'' % k for k in v['incomes'] if k in known_service}))
            if kwargs['recv_from'] == '[\'%s\']' % last_add_name:
                kwargs.pop('recv_from')
            kwargs['send_to'] = '[%s]' % (','.join({'\'%s\'' % k for k in v['outgoings'] if k in known_service}))

            known_service.add(k)
            last_add_name = k

            py_code.append('%s.add(%s)' % (
                ' ' * indent,
                ', '.join(
                    '%s=%s' % (kk, '\'%s\'' % vv if isinstance(vv, str)
                                                    and not vv.startswith('\'') and not vv.startswith('[')
                    else vv) for kk, vv
                    in
                    (list(kwargs.items()) + list(v['kwargs'].items())) if
                    vv and vv != '[]' and kk not in self._common_kwargs)))

        py_code[-1] += ')'

        py_code.extend(['',
                        '# build the flow and visualize it',
                        'f.build(backend=None).to_url()'
                        ])
        py_code.extend(['',
                        '# use this flow in multi-thread mode for indexing',
                        'with f.build(backend=\'thread\') as fl:',
                        '%sfl.index(txt_file=\'test.txt\')' % (' ' * indent)
                        ])
        py_code.append('')

        return '\n'.join(py_code)

    @build_required(BuildLevel.GRAPH)
    def to_mermaid(self, left_right: bool = True) -> str:
        """
        Output the mermaid graph for visualization

        :param left_right: render the flow in left-to-right manner, otherwise top-down manner.
        :return: a mermaid-formatted string
        """

        # fill, stroke
        service_color = {
            Service.Frontend: ('#FFE0E0', '#000'),
            Service.Router: ('#C9E8D2', '#000'),
            Service.Encoder: ('#FFDAAF', '#000'),
            Service.Preprocessor: ('#CED7EF', '#000'),
            Service.Indexer: ('#FFFBC1', '#000'),
        }

        mermaid_graph = OrderedDict()
        cls_dict = defaultdict(set)
        replicas_dict = {}

        for k, v in self._service_nodes.items():
            mermaid_graph[k] = []
            num_replicas = getattr(v['parsed_args'], 'num_parallel', 1)
            if num_replicas > 1:
                head_router = k + '_HEAD'
                tail_router = k + '_TAIL'
                replicas_dict[k] = (head_router, tail_router)
                cls_dict[Service.Router].add(head_router)
                cls_dict[Service.Router].add(tail_router)
                p_r = '((%s))'
                k_service = v['service']
                p_e = '((%s))' if k_service == Service.Router else '(%s)'

                mermaid_graph[k].append('subgraph %s["%s (replias=%d)"]' % (k, k, num_replicas))
                for j in range(num_replicas):
                    r = k + '_%d' % j
                    cls_dict[k_service].add(r)
                    mermaid_graph[k].append('\t%s%s-->%s%s' % (head_router, p_r % 'router', r, p_e % r))
                    mermaid_graph[k].append('\t%s%s-->%s%s' % (r, p_e % r, tail_router, p_r % 'router'))
                mermaid_graph[k].append('end')
                mermaid_graph[k].append(
                    'style %s fill:%s,stroke:%s,stroke-width:2px,stroke-dasharray:5,stroke-opacity:0.3,fill-opacity:0.5' % (
                        k, service_color[k_service][0], service_color[k_service][1]))

        for k, ed_type in self._service_edges.items():
            start_node, end_node = k.split('-')
            cur_node = mermaid_graph[start_node]

            s_service = self._service_nodes[start_node]['service']
            e_service = self._service_nodes[end_node]['service']

            start_node_text = start_node
            end_node_text = end_node

            # check if is in replicas
            if start_node in replicas_dict:
                start_node = replicas_dict[start_node][1]  # outgoing
                s_service = Service.Router
                start_node_text = 'router'
            if end_node in replicas_dict:
                end_node = replicas_dict[end_node][0]  # incoming
                e_service = Service.Router
                end_node_text = 'router'

            # always plot frontend at the start and the end
            if e_service == Service.Frontend:
                end_node_text = end_node
                end_node += '_END'

            cls_dict[s_service].add(start_node)
            cls_dict[e_service].add(end_node)
            p_s = '((%s))' if s_service == Service.Router else '(%s)'
            p_e = '((%s))' if e_service == Service.Router else '(%s)'
            cur_node.append('\t%s%s-- %s -->%s%s' % (
                start_node, p_s % start_node_text, ed_type,
                end_node, p_e % end_node_text))

        style = ['classDef %sCLS fill:%s,stroke:%s,stroke-width:1px;' % (k, v[0], v[1]) for k, v in
                 service_color.items()]
        class_def = ['class %s %sCLS;' % (','.join(v), k) for k, v in cls_dict.items()]
        mermaid_str = '\n'.join(
            ['graph %s' % ('LR' if left_right else 'TD')] + [ss for s in mermaid_graph.values() for ss in
                                                             s] + style + class_def)

        return mermaid_str

    @build_required(BuildLevel.GRAPH)
    def to_url(self, **kwargs) -> str:
        """
        Rendering the current flow as a url points to a SVG, it needs internet connection

        :param kwargs: keyword arguments of :py:meth:`to_mermaid`
        :return: the url points to a SVG
        """
        import base64
        mermaid_str = self.to_mermaid(**kwargs)
        encoded_str = base64.b64encode(bytes(mermaid_str, 'utf-8')).decode('utf-8')
        return 'https://mermaidjs.github.io/mermaid-live-editor/#/view/%s' % encoded_str

    @build_required(BuildLevel.GRAPH)
    def to_jpg(self, path: str = 'flow.jpg', **kwargs) -> None:
        """
        Rendering the current flow as a jpg image, this will call :py:meth:`to_mermaid` and it needs internet connection

        :param path: the file path of the image
        :param kwargs: keyword arguments of :py:meth:`to_mermaid`
        :return:
        """

        from urllib.request import Request, urlopen
        encoded_str = self.to_url().replace('https://mermaidjs.github.io/mermaid-live-editor/#/view/', '')
        self.logger.warning('jpg exporting relies on https://mermaid.ink/, but it is not very stable. '
                            'some syntax are not supported, please use with caution.')
        self.logger.info('downloading as jpg...')
        req = Request('https://mermaid.ink/img/%s' % encoded_str, headers={'User-Agent': 'Mozilla/5.0'})
        with open(path, 'wb') as fp:
            fp.write(urlopen(req).read())
        self.logger.info('done')

    def train(self, bytes_gen: Iterator[bytes] = None, **kwargs):
        """Do training on the current flow

        It will start a :py:class:`CLIClient` and call :py:func:`train`.

        Example,

        .. highlight:: python
        .. code-block:: python

            with f.build(backend='thread') as flow:
                flow.train(txt_file='aa.txt')
                flow.train(image_zip_file='aa.zip', batch_size=64)
                flow.train(video_zip_file='aa.zip')
                ...


        This will call the pre-built reader to read files into an iterator of bytes and feed to the flow.

        One may also build a reader/generator on your own.

        Example,

        .. highlight:: python
        .. code-block:: python

            def my_reader():
                for _ in range(10):
                    yield b'abcdfeg'   # each yield generates a document for training

            with f.build(backend='thread') as flow:
                flow.train(bytes_gen=my_reader())

        :param bytes_gen: An iterator of bytes. If not given, then you have to specify it in `kwargs`.
        :param kwargs: accepts all keyword arguments of `gnes client` CLI
        """
        self._get_client(bytes_gen, mode='train', **kwargs).start()

    def index(self, bytes_gen: Iterator[bytes] = None, **kwargs):
        """Do indexing on the current flow

        Example,

        .. highlight:: python
        .. code-block:: python

            with f.build(backend='thread') as flow:
                flow.index(txt_file='aa.txt')
                flow.index(image_zip_file='aa.zip', batch_size=64)
                flow.index(video_zip_file='aa.zip')
                ...


        This will call the pre-built reader to read files into an iterator of bytes and feed to the flow.

        One may also build a reader/generator on your own.

        Example,

        .. highlight:: python
        .. code-block:: python

            def my_reader():
                for _ in range(10):
                    yield b'abcdfeg'  # each yield generates a document to index

            with f.build(backend='thread') as flow:
                flow.index(bytes_gen=my_reader())

        It will start a :py:class:`CLIClient` and call :py:func:`index`.

        :param bytes_gen: An iterator of bytes. If not given, then you have to specify it in `kwargs`.
        :param kwargs: accepts all keyword arguments of `gnes client` CLI
        """
        self._get_client(bytes_gen, mode='index', **kwargs).start()

    def query(self, bytes_gen: Iterator[bytes] = None, **kwargs):
        """Do indexing on the current flow

        It will start a :py:class:`CLIClient` and call :py:func:`query`.


        Example,

        .. highlight:: python
        .. code-block:: python

            with f.build(backend='thread') as flow:
                flow.query(txt_file='aa.txt')
                flow.query(image_zip_file='aa.zip', batch_size=64)
                flow.query(video_zip_file='aa.zip')
                ...


        This will call the pre-built reader to read files into an iterator of bytes and feed to the flow.

        One may also build a reader/generator on your own.

        Example,

        .. highlight:: python
        .. code-block:: python

            def my_reader():
                for _ in range(10):
                    yield b'abcdfeg'   # each yield generates a query for searching

            with f.build(backend='thread') as flow:
                flow.query(bytes_gen=my_reader())

        :param bytes_gen: An iterator of bytes. If not given, then you have to specify it in `kwargs`.
        :param kwargs: accepts all keyword arguments of `gnes client` CLI
        """
        yield from self._get_client(bytes_gen, mode='query', **kwargs).query()

    @build_required(BuildLevel.RUNTIME)
    def _get_client(self, bytes_gen: Iterator[bytes] = None, **kwargs):
        from ..cli.parser import set_client_cli_parser
        from ..client.cli import CLIClient

        _, p_args, _ = self._get_parsed_args(self, CLIClient.__name__, set_client_cli_parser, kwargs)
        p_args.grpc_port = self._service_nodes[self._frontend]['parsed_args'].grpc_port
        p_args.grpc_host = self._service_nodes[self._frontend]['parsed_args'].grpc_host
        c = CLIClient(p_args, start_at_init=False)
        if bytes_gen:
            c.bytes_generator = bytes_gen
        return c

    def add_frontend(self, *args, **kwargs) -> 'Flow':
        """Add a frontend to the current flow, a shortcut of :py:meth:`add(Service.Frontend)`.
        Usually you dont need to call this function explicitly, a flow object contains a frontend service by default.
        This function is useful when you build a flow without the frontend and want to customize the frontend later.
        """
        return self.add(Service.Frontend, *args, **kwargs)

    def add_encoder(self, *args, **kwargs) -> 'Flow':
        """Add an encoder to the current flow, a shortcut of :py:meth:`add(Service.Encoder)`"""
        return self.add(Service.Encoder, *args, **kwargs)

    def add_indexer(self, *args, **kwargs) -> 'Flow':
        """Add an indexer to the current flow, a shortcut of :py:meth:`add(Service.Indexer)`"""
        return self.add(Service.Indexer, *args, **kwargs)

    def add_preprocessor(self, *args, **kwargs) -> 'Flow':
        """Add a preprocessor to the current flow, a shortcut of :py:meth:`add(Service.Preprocessor)`"""
        return self.add(Service.Preprocessor, *args, **kwargs)

    def add_router(self, *args, **kwargs) -> 'Flow':
        """Add a router to the current flow, a shortcut of :py:meth:`add(Service.Router)`"""
        return self.add(Service.Router, *args, **kwargs)

    def set_last_service(self, name: str, copy_flow: bool = True) -> 'Flow':
        """
        Set a service as the last service in the flow, useful when modifying the flow.

        :param name: the name of the existing service
        :param copy_flow: when set to true, then always copy the current flow and do the modification on top of it then return, otherwise, do in-line modification
        :return: a (new) flow object with modification
        """
        op_flow = copy.deepcopy(self) if copy_flow else self

        if name not in op_flow._service_nodes:
            raise FlowMissingNode('recv_from: %s can not be found in this Flow' % name)

        if op_flow._last_changed_service and name == op_flow._last_changed_service[-1]:
            pass
        else:
            op_flow._last_changed_service.append(name)

        # graph is now changed so we need to
        # reset the build level to the lowest
        op_flow._build_level = BuildLevel.EMPTY

        return op_flow

    def set(self, name: str, recv_from: Union[str, Tuple[str], List[str], 'Service'] = None,
            send_to: Union[str, Tuple[str], List[str], 'Service'] = None,
            copy_flow: bool = True,
            clear_old_attr: bool = False,
            as_last_service: bool = False,
            **kwargs) -> 'Flow':
        """
        Set the attribute of an existing service (added by :py:meth:`add`) in the flow.
        For the attributes or kwargs that aren't given, they will remain unchanged as before.

        :param name: the name of the existing service
        :param recv_from: the name of the service(s) that this service receives data from.
                           One can also use 'Service.Frontend' to indicate the connection with the frontend.
        :param send_to:  the name of the service(s) that this service sends data to.
                           One can also use 'Service.Frontend' to indicate the connection with the frontend.
        :param copy_flow: when set to true, then always copy the current flow and do the modification on top of it then return, otherwise, do in-line modification
        :param clear_old_attr: remove old attribute value before setting the new one
        :param as_last_service: whether setting the changed service as the last service in the graph
        :param kwargs: other keyword-value arguments that the service CLI supports
        :return: a (new) flow object with modification
        """
        op_flow = copy.deepcopy(self) if copy_flow else self

        if name not in op_flow._service_nodes:
            raise FlowMissingNode('recv_from: %s can not be found in this Flow' % name)

        node = op_flow._service_nodes[name]
        service = node['service']

        if recv_from:
            recv_from = op_flow._parse_service_endpoints(op_flow, name, recv_from, connect_to_last_service=True)

            if clear_old_attr:
                # remove all edges point to this service
                for n in op_flow._service_nodes.values():
                    if name in n['outgoings']:
                        n['outgoings'].remove(name)
                node['incomes'] = recv_from
            else:
                node['incomes'] = node['incomes'].union(recv_from)

            # add it the new edge back
            for s in recv_from:
                op_flow._service_nodes[s]['outgoings'].add(name)

        if send_to:
            send_to = op_flow._parse_service_endpoints(op_flow, name, send_to, connect_to_last_service=False)
            if clear_old_attr:
                # remove all edges this service point to
                for n in op_flow._service_nodes.values():
                    if name in n['incomes']:
                        n['incomes'].remove(name)
                node['outgoings'] = send_to
            else:
                node['outgoings'] = node['outgoings'].union(send_to)

            for s in send_to:
                op_flow._service_nodes[s]['incomes'].add(name)

        if kwargs:
            if not clear_old_attr:
                node['kwargs'].update(kwargs)
                kwargs = node['kwargs']
            args, p_args, unk_args = op_flow._get_parsed_args(op_flow, name, service_map[service]['parser'], kwargs)
            node.update({
                'args': args,
                'parsed_args': p_args,
                'kwargs': kwargs,
                'unk_args': unk_args
            })

        if as_last_service:
            op_flow.set_last_service(name, False)

        # graph is now changed so we need to
        # reset the build level to the lowest
        op_flow._build_level = BuildLevel.EMPTY

        return op_flow

    def remove(self, name: str = None, copy_flow: bool = True) -> 'Flow':
        """
        Remove a service from the flow.

        :param name: the name of the existing service
        :param copy_flow: when set to true, then always copy the current flow and do the modification on top of it then return, otherwise, do in-line modification
        :return: a (new) flow object with modification
        """

        op_flow = copy.deepcopy(self) if copy_flow else self

        if name not in op_flow._service_nodes:
            raise FlowMissingNode('recv_from: %s can not be found in this Flow' % name)

        op_flow._service_nodes.pop(name)

        # remove all edges point to this service
        for n in op_flow._service_nodes.values():
            if name in n['outgoings']:
                n['outgoings'].remove(name)
            if name in n['incomes']:
                n['incomes'].remove(name)

        if op_flow._service_nodes:
            op_flow._last_changed_service = [v for v in op_flow._last_changed_service if v != name]
        else:
            op_flow._last_changed_service = []

        # graph is now changed so we need to
        # reset the build level to the lowest
        op_flow._build_level = BuildLevel.EMPTY

        return op_flow

    def add(self, service: Union['Service', str],
            name: str = None,
            recv_from: Union[str, Tuple[str], List[str], 'Service'] = None,
            send_to: Union[str, Tuple[str], List[str], 'Service'] = None,
            copy_flow: bool = True,
            **kwargs) -> 'Flow':
        """
        Add a service to the current flow object and return the new modified flow object.
        The attribute of the service can be later changed with :py:meth:`set` or deleted with :py:meth:`remove`

        Note there are shortcut versions of this method.
        Recommend to use :py:meth:`add_encoder`, :py:meth:`add_preprocessor`,
        :py:meth:`add_router`, :py:meth:`add_indexer` whenever possible.

        :param service: a 'Service' enum or string, possible choices: Encoder, Router, Preprocessor, Indexer, Frontend
        :param name: the name identifier of the service, can be used in 'recv_from',
                    'send_to', :py:meth:`set` and :py:meth:`remove`.
        :param recv_from: the name of the service(s) that this service receives data from.
                           One can also use 'Service.Frontend' to indicate the connection with the frontend.
        :param send_to:  the name of the service(s) that this service sends data to.
                           One can also use 'Service.Frontend' to indicate the connection with the frontend.
        :param copy_flow: when set to true, then always copy the current flow and do the modification on top of it then return, otherwise, do in-line modification
        :param kwargs: other keyword-value arguments that the service CLI supports
        :return: a (new) flow object with modification
        """

        op_flow = copy.deepcopy(self) if copy_flow else self

        if isinstance(service, str):
            service = Service.from_string(service)

        if service not in service_map:
            raise ValueError('service: %s is not supported, should be one of %s' % (service, service_map.keys()))

        if name in op_flow._service_nodes:
            raise FlowTopologyError('name: %s is used in this Flow already!' % name)
        if not name:
            name = '%s%d' % (service, op_flow._service_name_counter[service])
            op_flow._service_name_counter[service] += 1
        if not name.isidentifier():
            raise ValueError('name: %s is invalid, please follow the python variable name conventions' % name)

        if service == Service.Frontend:
            if op_flow._frontend:
                raise FlowTopologyError('frontend is already in this Flow')
            op_flow._frontend = name

        recv_from = op_flow._parse_service_endpoints(op_flow, name, recv_from, connect_to_last_service=True)
        send_to = op_flow._parse_service_endpoints(op_flow, name, send_to, connect_to_last_service=False)

        args, p_args, unk_args = op_flow._get_parsed_args(op_flow, name, service_map[service]['parser'], kwargs)

        op_flow._service_nodes[name] = {
            'service': service,
            'parsed_args': p_args,
            'args': args,
            'incomes': recv_from,
            'outgoings': send_to,
            'kwargs': kwargs,
            'unk_args': unk_args
        }

        # direct all income services' output to the current service
        for s in recv_from:
            op_flow._service_nodes[s]['outgoings'].add(name)
        for s in send_to:
            op_flow._service_nodes[s]['incomes'].add(name)

        op_flow.set_last_service(name, False)

        # graph is now changed so we need to
        # reset the build level to the lowest
        op_flow._build_level = BuildLevel.EMPTY

        return op_flow

    @staticmethod
    def _parse_service_endpoints(op_flow, cur_service_name, service_endpoint, connect_to_last_service=False,
                                 check_name_exist=True):
        # parsing recv_from
        if isinstance(service_endpoint, str):
            service_endpoint = [service_endpoint]
        elif service_endpoint == Service.Frontend:
            service_endpoint = [op_flow._frontend]
        elif not service_endpoint:
            if op_flow._last_changed_service and connect_to_last_service:
                service_endpoint = [op_flow._last_changed_service[-1]]
            else:
                service_endpoint = []
        if isinstance(service_endpoint, list) or isinstance(service_endpoint, tuple):
            for s in service_endpoint:
                if s == cur_service_name:
                    raise FlowTopologyError('the income of a service can not be itself')
                if s not in op_flow._service_nodes:
                    if check_name_exist:
                        raise FlowMissingNode('recv_from: %s can not be found in this Flow' % s)
        else:
            raise ValueError('recv_from=%s is not parsable' % service_endpoint)
        return set(service_endpoint)

    @staticmethod
    def _get_parsed_args(op_flow, name, service_arg_parser, kwargs):
        kwargs.update(op_flow._common_kwargs)
        args = []
        for k, v in kwargs.items():
            if isinstance(v, bool):
                if v:
                    if not k.startswith('no_') and not k.startswith('no-'):
                        args.append('--%s' % k)
                    else:
                        args.append('--%s' % k[3:])
                else:
                    if k.startswith('no_') or k.startswith('no-'):
                        args.append('--%s' % k)
                    else:
                        args.append('--no_%s' % k)
            else:
                args.extend(['--%s' % k, str(v)])
        try:
            p_args, unknown_args = service_arg_parser().parse_known_args(args)
            if unknown_args:
                op_flow.logger.warning('not sure what these arguments are: %s' % unknown_args)
        except SystemExit:
            raise ValueError('bad arguments for service "%s", '
                             'you may want to double check your args "%s"' % (name, args))
        return args, p_args, unknown_args

    def _build_graph(self, copy_flow: bool) -> 'Flow':
        op_flow = copy.deepcopy(self) if copy_flow else self

        op_flow._service_edges.clear()

        if not op_flow._frontend:
            raise FlowIncompleteError('frontend does not exist, you may need to add_frontend()')

        if not op_flow._last_changed_service or not op_flow._service_nodes:
            raise FlowTopologyError('flow is empty?')

        # close the loop
        op_flow._service_nodes[op_flow._frontend]['incomes'] = {op_flow._last_changed_service[-1]}

        # build all edges
        for k, v in op_flow._service_nodes.items():
            for s in v['incomes']:
                op_flow._service_edges['%s-%s' % (s, k)] = ''
            for t in v['outgoings']:
                op_flow._service_edges['%s-%s' % (k, t)] = ''

        for k in op_flow._service_edges.keys():
            start_node, end_node = k.split('-')
            edges_with_same_start = [ed for ed in op_flow._service_edges.keys() if ed.startswith(start_node)]
            edges_with_same_end = [ed for ed in op_flow._service_edges.keys() if ed.endswith(end_node)]

            s_pargs = op_flow._service_nodes[start_node]['parsed_args']
            e_pargs = op_flow._service_nodes[end_node]['parsed_args']

            # Rule
            # if a node has multiple income/outgoing services,
            # then its socket_in/out must be PULL_BIND or PUB_BIND
            # otherwise it should be different than its income
            # i.e. income=BIND => this=CONNECT, income=CONNECT => this = BIND
            #
            # when a socket is BIND, then host must NOT be set, aka default host 0.0.0.0
            # host_in and host_out is only set when corresponding socket is CONNECT

            if len(edges_with_same_start) > 1 and len(edges_with_same_end) == 1:
                s_pargs.socket_out = SocketType.PUB_BIND
                s_pargs.host_out = BaseService.default_host
                e_pargs.socket_in = SocketType.SUB_CONNECT
                e_pargs.host_in = start_node
                e_pargs.port_in = s_pargs.port_out
                op_flow._service_edges[k] = 'PUB-sub'
            elif len(edges_with_same_end) > 1 and len(edges_with_same_start) == 1:
                s_pargs.socket_out = SocketType.PUSH_CONNECT
                s_pargs.host_out = end_node
                e_pargs.socket_in = SocketType.PULL_BIND
                e_pargs.host_in = BaseService.default_host
                s_pargs.port_out = e_pargs.port_in
                op_flow._service_edges[k] = 'push-PULL'
            elif len(edges_with_same_start) == 1 and len(edges_with_same_end) == 1:
                # in this case, either side can be BIND
                # we prefer frontend to be always BIND
                # check if either node is frontend
                if start_node == op_flow._frontend:
                    s_pargs.socket_out = SocketType.PUSH_BIND
                    e_pargs.socket_in = SocketType.PULL_CONNECT
                elif end_node == op_flow._frontend:
                    s_pargs.socket_out = SocketType.PUSH_CONNECT
                    e_pargs.socket_in = SocketType.PULL_BIND
                else:
                    e_pargs.socket_in = s_pargs.socket_out.paired

                if s_pargs.socket_out.is_bind:
                    s_pargs.host_out = BaseService.default_host
                    e_pargs.host_in = start_node
                    e_pargs.port_in = s_pargs.port_out
                    op_flow._service_edges[k] = 'PUSH-pull'
                elif e_pargs.socket_in.is_bind:
                    s_pargs.host_out = end_node
                    e_pargs.host_in = BaseService.default_host
                    s_pargs.port_out = e_pargs.port_in
                    op_flow._service_edges[k] = 'push-PULL'
                else:
                    raise FlowTopologyError('edge %s -> %s is ambiguous, at least one socket should be BIND')
            else:
                raise FlowTopologyError('found %d edges start with %s and %d edges end with %s, '
                                        'this type of topology is ambiguous and should not exist, '
                                        'i can not determine the socket type' % (
                                            len(edges_with_same_start), start_node, len(edges_with_same_end), end_node))

        op_flow._build_level = BuildLevel.GRAPH
        return op_flow

    def build(self, backend: Optional[str] = 'process', copy_flow: bool = False, *args, **kwargs) -> 'Flow':
        """
        Build the current flow and make it ready to use

        :param backend: supported 'thread', 'process', 'swarm', 'k8s', 'shell', if None then only build graph only
        :param copy_flow: return the copy of the current flow
        :return: the current flow (by default)
        """

        op_flow = self._build_graph(copy_flow)

        if not backend:
            op_flow.logger.warning('no specified backend, build_level stays at %s, '
                                   'and you can not run this flow.' % op_flow._build_level)
        elif backend in {'thread', 'process'}:
            op_flow._service_contexts.clear()
            for v in op_flow._service_nodes.values():
                p_args = v['parsed_args']
                p_args.parallel_backend = backend
                # for thread and process backend which runs locally, host_in and host_out should not be set
                p_args.host_in = BaseService.default_host
                p_args.host_out = BaseService.default_host
                op_flow._service_contexts.append((service_map[v['service']]['builder'], p_args))
            op_flow._build_level = BuildLevel.RUNTIME
        else:
            raise NotImplementedError('backend=%s is not supported yet' % backend)

        return op_flow

    def __call__(self, *args, **kwargs):
        return self.build(*args, **kwargs)

    def __enter__(self):
        if self._build_level.value < BuildLevel.RUNTIME.value:
            self.logger.warning(
                'current build_level=%s, lower than required. '
                'build the flow now via build() with default parameters' % self._build_level)
            self.build(copy_flow=False)
        self._service_stack = ExitStack()
        for k, v in self._service_contexts:
            self._service_stack.enter_context(k(v))

        self.logger.critical('flow is built and ready, current build level is %s' % self._build_level)
        return self

    def close(self):
        if hasattr(self, '_service_stack'):
            self._service_stack.close()
        self._build_level = BuildLevel.EMPTY
        self.logger.critical(
            'flow is closed and all resources should be released already, current build level is %s' % self._build_level)

    def __eq__(self, other):
        """
        Comparing the topology of a flow with another flow.
        Identification is defined by whether two flows share the same set of edges.

        :param other: the second flow object
        :return:
        """

        if self._build_level.value < BuildLevel.GRAPH.value:
            a = self.build(backend=None, copy_flow=True)
        else:
            a = self

        if other._build_level.value < BuildLevel.GRAPH.value:
            b = other.build(backend=None, copy_flow=True)
        else:
            b = other

        return a._service_edges == b._service_edges

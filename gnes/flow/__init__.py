import copy
import os
from collections import OrderedDict, defaultdict
from contextlib import ExitStack
from functools import wraps
from typing import Union, Tuple, List, Optional, Iterator

from ..cli.parser import set_router_parser, set_indexer_parser, \
    set_frontend_parser, set_preprocessor_parser, \
    set_encoder_parser, set_client_cli_parser
from ..client.cli import CLIClient
from ..helper import set_logger
from ..service.base import SocketType, BaseService, BetterEnum, ServiceManager
from ..service.encoder import EncoderService
from ..service.frontend import FrontendService
from ..service.indexer import IndexerService
from ..service.preprocessor import PreprocessorService
from ..service.router import RouterService


class Service(BetterEnum):
    Frontend = 0
    Encoder = 1
    Router = 2
    Indexer = 3
    Preprocessor = 4


class FlowImcompleteError(ValueError):
    """Exception when the flow missing some important component to run"""


class FlowTopologyError(ValueError):
    """Exception when the topology is ambiguous"""


class FlowBuildLevelMismatch(ValueError):
    """Exception when required level is higher than the current build level"""


def _build_level(required_level: 'Flow.BuildLevel'):
    def __build_level(func):
        @wraps(func)
        def arg_wrapper(self, *args, **kwargs):
            if hasattr(self, '_build_level'):
                if self._build_level.value >= required_level.value:
                    return func(self, *args, **kwargs)
                else:
                    raise FlowBuildLevelMismatch(
                        'build_level check failed for %r, required level: %s, actual level: %s' % (
                            func, required_level, self._build_level))
            else:
                raise AttributeError('%r has no attribute "_build_level"' % self)

        return arg_wrapper

    return __build_level


class Flow:
    """
    GNES Flow: an intuitive way to build workflow for GNES.

    You can use :py:meth:`.add()` then :py:meth:`.build()` to customize your own workflow.
    For example:

    .. highlight:: python
    .. code-block:: python

        from gnes.flow import Flow, Service as gfs

        f = (Flow(check_version=False, route_table=True)
             .add(gfs.Preprocessor, yaml_path='BasePreprocessor')
             .add(gfs.Encoder, yaml_path='BaseEncoder')
             .add(gfs.Router, yaml_path='BaseRouter'))

        with f.build(backend='thread') as flow:
            flow.index()
            ...

    You can also use the shortcuts, e.g. :py:meth:`add_encoder`, :py:meth:`add_preprocessor`.

    It is recommend to use flow in the context manner as showed above.

    Note the different default copy behaviors in :py:meth:`.add()` and :py:meth:`.build()`:
    :py:meth:`.add()` always copy the flow by default, whereas :py:meth:`.build()` modify the flow in place.
    You can change this behavior by giving an argument `copy_flow=False`.

    """
    _supported_orch = {'swarm', 'k8s'}
    _service2parser = {
        Service.Encoder: set_encoder_parser,
        Service.Router: set_router_parser,
        Service.Indexer: set_indexer_parser,
        Service.Frontend: set_frontend_parser,
        Service.Preprocessor: set_preprocessor_parser,
    }
    _service2builder = {
        Service.Encoder: lambda x: ServiceManager(EncoderService, x),
        Service.Router: lambda x: ServiceManager(RouterService, x),
        Service.Indexer: lambda x: ServiceManager(IndexerService, x),
        Service.Preprocessor: lambda x: ServiceManager(PreprocessorService, x),
        Service.Frontend: FrontendService,
    }

    class BuildLevel(BetterEnum):
        EMPTY = 0
        GRAPH = 1
        RUNTIME = 2

    def __init__(self, with_frontend: bool = True, **kwargs):
        self.logger = set_logger(self.__class__.__name__)
        self._service_nodes = OrderedDict()
        self._service_edges = {}
        self._service_name_counter = {k: 0 for k in Flow._service2parser.keys()}
        self._service_contexts = []
        self._last_add_service = None
        self._common_kwargs = kwargs
        self._frontend = None
        self._client = None
        self._build_level = Flow.BuildLevel.EMPTY
        self._backend = None
        if with_frontend:
            self.add_frontend(copy_flow=False)
        else:
            self.logger.warning('with_frontend is set to False, you need to add_frontend() by yourself')

    @_build_level(BuildLevel.GRAPH)
    def to_yaml(self, orchestration: str) -> str:
        if orchestration not in Flow._supported_orch:
            raise TypeError(
                '%s is not valid type of orchestration, should be one of %s' % (orchestration, Flow._supported_orch))

    @staticmethod
    def from_yaml(orchestration: str) -> 'Flow':
        if orchestration not in Flow._supported_orch:
            raise TypeError(
                '%s is not valid type of orchestration, should be one of %s' % (orchestration, Flow._supported_orch))

    @_build_level(BuildLevel.GRAPH)
    def to_mermaid(self, left_right: bool = True):
        """
        Output the mermaid graph for visualization

        :param left_right: render the flow in left-to-right manner, otherwise top-down manner.
        :return:
        """
        mermaid_graph = OrderedDict()
        for k in self._service_nodes.keys():
            mermaid_graph[k] = []
        cls_dict = defaultdict(set)

        for k, ed_type in self._service_edges.items():
            start_node, end_node = k.split('-')
            s_service = self._service_nodes[start_node]['service']
            e_service = self._service_nodes[end_node]['service']
            cls_dict[s_service].add(start_node)
            cls_dict[e_service].add(end_node)
            p_s = '((%s))' if s_service == Service.Router else '(%s)'
            p_e = '((%s))' if e_service == Service.Router else '(%s)'
            mermaid_graph[start_node].append('\t%s%s-- %s -->%s%s' % (
                start_node, p_s % start_node, ed_type,
                end_node, p_e % end_node))

        style = ['classDef FrontendCLS fill:#FFE0E0,stroke:#FFE0E0,stroke-width:1px;',
                 'classDef EncoderCLS fill:#FFDAAF,stroke:#FFDAAF,stroke-width:1px;',
                 'classDef IndexerCLS fill:#FFFBC1,stroke:#FFFBC1,stroke-width:1px;',
                 'classDef RouterCLS fill:#C9E8D2,stroke:#C9E8D2,stroke-width:1px;',
                 'classDef PreprocessorCLS fill:#CEEEEF,stroke:#CEEEEF,stroke-width:1px;']
        class_def = ['class %s %sCLS;' % (','.join(v), k) for k, v in cls_dict.items()]
        mermaid_str = '\n'.join(
            ['graph %s' % ('LR' if left_right else 'TD')] + [ss for s in mermaid_graph.values() for ss in
                                                             s] + style + class_def)

        return mermaid_str

    @_build_level(BuildLevel.GRAPH)
    def to_jpg(self, path: str = 'flow.jpg', left_right: bool = True):
        """
        Rendering the current flow as a jpg image, this will call :py:meth:`to_mermaid` and it needs internet connection

        :param path: the file path of the image
        :param left_right: render the flow in left-to-right manner, otherwise top-down manner.
        :return:
        """
        import base64
        from urllib.request import Request, urlopen
        mermaid_str = self.to_mermaid(left_right)
        encoded_str = base64.b64encode(bytes(mermaid_str, 'utf-8')).decode('utf-8')
        print('https://mermaidjs.github.io/mermaid-live-editor/#/view/%s' % encoded_str)
        self.logger.info('saving jpg...')
        req = Request('https://mermaid.ink/img/%s' % encoded_str, headers={'User-Agent': 'Mozilla/5.0'})
        with open(path, 'wb') as fp:
            fp.write(urlopen(req).read())
        self.logger.info('done')

    def train(self, bytes_gen: Iterator[bytes] = None, **kwargs):
        """Do training on the current flow

        It will start a :py:class:`CLIClient` and call :py:func:`train`.

        :param bytes_gen: An iterator of bytes. If not given, then you have to specify it in `kwargs`.
        :param kwargs: accepts all keyword arguments of `gnes client` CLI
        """
        self._call_client(bytes_gen, mode='train', **kwargs)

    def index(self, bytes_gen: Iterator[bytes] = None, **kwargs):
        """Do indexing on the current flow

        It will start a :py:class:`CLIClient` and call :py:func:`index`.

        :param bytes_gen: An iterator of bytes. If not given, then you have to specify it in `kwargs`.
        :param kwargs: accepts all keyword arguments of `gnes client` CLI
        """
        self._call_client(bytes_gen, mode='index', **kwargs)

    def query(self, bytes_gen: Iterator[bytes] = None, **kwargs):
        """Do indexing on the current flow

        It will start a :py:class:`CLIClient` and call :py:func:`query`.

        :param bytes_gen: An iterator of bytes. If not given, then you have to specify it in `kwargs`.
        :param kwargs: accepts all keyword arguments of `gnes client` CLI
        """
        self._call_client(bytes_gen, mode='query', **kwargs)

    @_build_level(BuildLevel.RUNTIME)
    def _call_client(self, bytes_gen: Iterator[bytes] = None, **kwargs):
        os.unsetenv('http_proxy')
        os.unsetenv('https_proxy')
        args, p_args = self._get_parsed_args(self, set_client_cli_parser, kwargs)
        p_args.grpc_port = self._service_nodes[self._frontend]['parsed_args'].grpc_port
        p_args.grpc_host = self._service_nodes[self._frontend]['parsed_args'].grpc_host
        c = CLIClient(p_args, start_at_init=False)
        if bytes_gen:
            c.bytes_generator = bytes_gen
        c.start()

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

    def add(self, service: 'Service',
            name: str = None,
            service_in: Union[str, Tuple[str], List[str], 'Service'] = None,
            service_out: Union[str, Tuple[str], List[str], 'Service'] = None,
            copy_flow: bool = True,
            **kwargs) -> 'Flow':
        """
        Add a service to the current flow object and return the new modified flow object

        :param service: a 'Service' enum, possible choices: Encoder, Router, Preprocessor, Indexer, Frontend
        :param name: the name indentifier of the service, useful in 'service_in' and 'service_out'
        :param service_in: the name of the service(s) that this service receives data from.
                           One can also use 'Service.Frontend' to indicate the connection with the frontend.
        :param service_out:  the name of the service(s) that this service sends data to.
                           One can also use 'Service.Frontend' to indicate the connection with the frontend.
        :param copy_flow: when set to true, then always copy the current flow and do the modification on top of it then return, otherwise, do in-line modification
        :param kwargs: other keyword-value arguments that the service CLI supports
        :return: a (new) flow object with modification
        """

        op_flow = copy.deepcopy(self) if copy_flow else self

        if service not in Flow._service2parser:
            raise ValueError('service: %s is not supported, should be one of %s' % (service, Flow._service2parser))

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

        service_in = op_flow._parse_service_endpoints(op_flow, name, service_in, connect_to_last_service=True)
        service_out = op_flow._parse_service_endpoints(op_flow, name, service_out, connect_to_last_service=False)

        args, p_args = op_flow._get_parsed_args(op_flow, Flow._service2parser[service], kwargs)

        op_flow._service_nodes[name] = {
            'service': service,
            'parsed_args': p_args,
            'args': args,
            'incomes': service_in,
            'outgoings': service_out}

        # direct all income services' output to the current service
        for s in service_in:
            op_flow._service_nodes[s]['outgoings'].add(name)
        for s in service_out:
            op_flow._service_nodes[s]['incomes'].add(name)

        op_flow._last_add_service = name

        # graph is now changed so we need to
        # reset the build level to the lowest
        op_flow._build_level = Flow.BuildLevel.EMPTY

        return op_flow

    @staticmethod
    def _parse_service_endpoints(op_flow, cur_service_name, service_endpoint, connect_to_last_service=False):
        # parsing service_in
        if isinstance(service_endpoint, str):
            service_endpoint = [service_endpoint]
        elif service_endpoint == Service.Frontend:
            service_endpoint = [op_flow._frontend]
        elif not service_endpoint:
            if op_flow._last_add_service and connect_to_last_service:
                service_endpoint = [op_flow._last_add_service]
            else:
                service_endpoint = []
        if isinstance(service_endpoint, list) or isinstance(service_endpoint, tuple):
            for s in service_endpoint:
                if s == cur_service_name:
                    raise FlowTopologyError('the income of a service can not be itself')
                if s not in op_flow._service_nodes:
                    raise FlowTopologyError('service_in: %s can not be found in this Flow' % s)
        else:
            raise ValueError('service_in=%s is not parsable' % service_endpoint)
        return set(service_endpoint)

    @staticmethod
    def _get_parsed_args(op_flow, service_arg_parser, kwargs):
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
                             'you may want to double check your args "%s"' % (service_arg_parser, args))
        return args, p_args

    def _build_graph(self, copy_flow: bool) -> 'Flow':
        op_flow = copy.deepcopy(self) if copy_flow else self

        op_flow._service_edges.clear()

        if not op_flow._frontend:
            raise FlowImcompleteError('frontend does not exist, you may need to add_frontend()')

        if not op_flow._last_add_service or not op_flow._service_nodes:
            raise FlowTopologyError('flow is empty?')

        # close the loop
        op_flow._service_nodes[op_flow._frontend]['incomes'].add(op_flow._last_add_service)

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

        op_flow._build_level = Flow.BuildLevel.GRAPH
        return op_flow

    def build(self, backend: Optional[str] = 'thread', copy_flow: bool = False, *args, **kwargs) -> 'Flow':
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
                op_flow._service_contexts.append((Flow._service2builder[v['service']], p_args))
            op_flow._build_level = Flow.BuildLevel.RUNTIME
        else:
            raise NotImplementedError('backend=%s is not supported yet' % backend)

        return op_flow

    def __call__(self, *args, **kwargs):
        return self.build(*args, **kwargs)

    def __enter__(self):
        if self._build_level.value < Flow.BuildLevel.RUNTIME.value:
            self.logger.warning(
                'current build_level=%s, lower than required. '
                'build the flow now via build() with default parameters' % self._build_level)
            self.build(copy_flow=False)
        self._service_stack = ExitStack()
        for k, v in self._service_contexts:
            self._service_stack.enter_context(k(v))

        self.logger.critical('flow is built and ready, current build level is %s' % self._build_level)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        if hasattr(self, '_service_stack'):
            self._service_stack.close()
        self._build_level = Flow.BuildLevel.EMPTY
        self.logger.critical(
            'flow is closed and all resources should be released already, current build level is %s' % self._build_level)

    def __getstate__(self):
        d = dict(self.__dict__)
        del d['logger']
        return d

    def __setstate__(self, d):
        self.__dict__.update(d)
        self.logger = set_logger(self.__class__.__name__)

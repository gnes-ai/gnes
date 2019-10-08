from collections import OrderedDict, defaultdict
from contextlib import ExitStack
from functools import wraps
from typing import Union, Tuple, List

from ..cli.parser import set_router_parser, set_indexer_parser, \
    set_frontend_parser, set_preprocessor_parser, \
    set_encoder_parser
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


def _build_level(required_level: 'Flow.BuildLevel'):
    def __build_level(func):
        @wraps(func)
        def arg_wrapper(self, *args, **kwargs):
            if hasattr(self, '_build_level'):
                if self._build_level.value >= required_level.value:
                    return func(self, *args, **kwargs)
                else:
                    raise ValueError('build_level check failed for %s, required: %s, actual: %s' % (
                        func.__name__, required_level, self._build_level))
            else:
                raise AttributeError('%r has no attribute "_build_level"' % self)

        return arg_wrapper

    return __build_level


class Flow:
    _supported_orch = {'swarm', 'k8s'}
    _service2parser = {
        Service.Encoder: set_encoder_parser(),
        Service.Router: set_router_parser(),
        Service.Indexer: set_indexer_parser(),
        Service.Frontend: set_frontend_parser(),
        Service.Preprocessor: set_preprocessor_parser(),
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
        self._service_name_counter = {k: 0 for k in self._service2parser.keys()}
        self._service_contexts = []
        self._last_add_service = None
        self._common_kwargs = kwargs
        self._frontend = None
        self._client = None
        self._build_level = Flow.BuildLevel.EMPTY
        self._backend = None
        if with_frontend:
            self.add_frontend()
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

        self.logger.info(
            'copy-paste the output and visualize it with: https://mermaidjs.github.io/mermaid-live-editor/')
        return mermaid_str

    def train(self):
        pass

    def index(self):
        pass

    def query(self):
        pass

    def add_frontend(self, *args, **kwargs) -> 'Flow':
        """Add a frontend to the current flow, a shortcut of add(Service.Frontend)
        Usually you dont need to call this function explicitly, a flow object contains a frontend service by default.
        This function is useful when you build a flow without the frontend and want to customize the frontend later.
        """
        return self.add(Service.Frontend, *args, **kwargs)

    def add_encoder(self, *args, **kwargs) -> 'Flow':
        """Add an encoder to the current flow, a shortcut of add(Service.Encoder)"""
        return self.add(Service.Encoder, *args, **kwargs)

    def add_indexer(self, *args, **kwargs) -> 'Flow':
        """Add an indexer to the current flow, a shortcut of add(Service.Indexer)"""
        return self.add(Service.Indexer, *args, **kwargs)

    def add_preprocessor(self, *args, **kwargs) -> 'Flow':
        """Add a router to the current flow, a shortcut of add(Service.Preprocessor)"""
        return self.add(Service.Preprocessor, *args, **kwargs)

    def add_router(self, *args, **kwargs) -> 'Flow':
        """Add a preprocessor to the current flow, a shortcut of add(Service.Router)"""
        return self.add(Service.Router, *args, **kwargs)

    def add(self, service: 'Service',
            name: str = None,
            service_in: Union[str, Tuple[str], List[str], 'Service'] = None,
            service_out: Union[str, Tuple[str], List[str], 'Service'] = None,
            **kwargs) -> 'Flow':
        """
        Add a service to the current flow object
        :param service: a 'Service' enum, possible choices: Encoder, Router, Preprocessor, Indexer, Frontend
        :param name: the name indentifier of the service, useful in 'service_in' and 'service_out'
        :param service_in: the name of the service(s) that this service receives data from.
                           One can also use 'Service.Frontend' to indicate the connection with the frontend.
        :param service_out:  the name of the service(s) that this service sends data to.
                           One can also use 'Service.Frontend' to indicate the connection with the frontend.
        :param kwargs: other keyword-value arguments that the service CLI supports
        :return: the current flow object
        """

        if service not in Flow._service2parser:
            raise ValueError('service: %s is not supported, should be one of %s' % (service, self._service2parser))

        if name in self._service_nodes:
            raise ValueError('name: %s is used in this Flow already!' % name)
        if not name:
            name = '%s%d' % (service, self._service_name_counter[service])
            self._service_name_counter[service] += 1
        if not name.isidentifier():
            raise ValueError('name: %s is invalid, please follow the python variable name conventions' % name)

        if service == Service.Frontend:
            if self._frontend:
                raise ValueError('frontend is already in this Flow')
            self._frontend = name

        service_in = self._parse_service_endpoints(name, service_in, connect_to_last_service=True)
        service_out = self._parse_service_endpoints(name, service_out, connect_to_last_service=False)

        args, p_args = self._get_parsed_args(service, kwargs)

        self._service_nodes[name] = {
            'service': service,
            'parsed_args': p_args,
            'args': args,
            'incomes': service_in,
            'outgoings': service_out}

        # direct all income services' output to the current service
        for s in service_in:
            self._service_nodes[s]['outgoings'].add(name)
        for s in service_out:
            self._service_nodes[s]['incomes'].add(name)

        self._last_add_service = name

        return self

    def _parse_service_endpoints(self, cur_service_name, service_endpoint, connect_to_last_service=False):
        # parsing service_in
        if isinstance(service_endpoint, str):
            service_endpoint = [service_endpoint]
        elif service_endpoint == Service.Frontend:
            service_endpoint = [self._frontend]
        elif not service_endpoint:
            if self._last_add_service and connect_to_last_service:
                service_endpoint = [self._last_add_service]
            else:
                service_endpoint = []
        if isinstance(service_endpoint, list) or isinstance(service_endpoint, tuple):
            for s in service_endpoint:
                if s == cur_service_name:
                    raise ValueError('the income of a service can not be itself')
                if s not in self._service_nodes:
                    raise ValueError('service_in: %s can not be found in this Flow' % s)
        else:
            raise ValueError('service_in=%s is not parsable' % service_endpoint)
        return set(service_endpoint)

    def _get_parsed_args(self, service, kwargs):
        kwargs.update(self._common_kwargs)
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
            p_args, unknown_args = Flow._service2parser[service].parse_known_args(args)
            if unknown_args:
                self.logger.warning('not sure what these arguments are: %s' % unknown_args)
        except SystemExit:
            raise ValueError('bad arguments for service "%s", '
                             'you may want to double check your args "%s"' % (service, args))
        return args, p_args

    def _build_graph(self) -> 'Flow':
        if not self._frontend:
            raise ValueError('frontend does not exist, you may need to add_frontend()')

        if not self._last_add_service or not self._service_nodes:
            raise ValueError('flow is empty?')

        # close the loop
        self._service_nodes[self._frontend]['incomes'].add(self._last_add_service)

        # build all edges
        for k, v in self._service_nodes.items():
            for s in v['incomes']:
                self._service_edges['%s-%s' % (s, k)] = ''
            for t in v['outgoings']:
                self._service_edges['%s-%s' % (k, t)] = ''

        for k in self._service_edges.keys():
            start_node, end_node = k.split('-')
            edges_with_same_start = [ed for ed in self._service_edges.keys() if ed.startswith(start_node)]
            edges_with_same_end = [ed for ed in self._service_edges.keys() if ed.endswith(end_node)]

            s_pargs = self._service_nodes[start_node]['parsed_args']
            e_pargs = self._service_nodes[end_node]['parsed_args']

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
                self._service_edges[k] = 'PUB-sub'
            elif len(edges_with_same_end) > 1 and len(edges_with_same_start) == 1:
                s_pargs.socket_out = SocketType.PUSH_CONNECT
                s_pargs.host_out = end_node
                e_pargs.socket_in = SocketType.PULL_BIND
                e_pargs.host_in = BaseService.default_host
                self._service_edges[k] = 'push-PULL'
            elif len(edges_with_same_start) == 1 and len(edges_with_same_end) == 1:
                # in this case, either side can be BIND
                # we prefer frontend to be always BIND
                # check if either node is frontend
                if start_node == self._frontend:
                    s_pargs.socket_out = SocketType.PUSH_BIND
                    e_pargs.socket_in = SocketType.PULL_CONNECT
                elif end_node == self._frontend:
                    s_pargs.socket_out = SocketType.PUSH_CONNECT
                    e_pargs.socket_in = SocketType.PULL_BIND
                else:
                    e_pargs.socket_in = s_pargs.socket_out.complement

                if s_pargs.socket_out.is_bind:
                    s_pargs.host_out = BaseService.default_host
                    e_pargs.host_in = start_node
                    self._service_edges[k] = 'PUSH-pull'
                elif e_pargs.socket_in.is_bind:
                    s_pargs.host_out = end_node
                    e_pargs.host_in = BaseService.default_host
                    self._service_edges[k] = 'push-PULL'
                else:
                    raise ValueError('edge %s -> %s is ambiguous, at least one socket should be BIND')
            else:
                raise ValueError('found %d edges start with %s and %d edges end with %s, '
                                 'this type of topology is ambiguous and should not exist, i can not determine the socket type' % (
                                     len(edges_with_same_start), start_node, len(edges_with_same_end), end_node))

        self._build_level = Flow.BuildLevel.GRAPH
        return self

    def build(self, backend='thread', *args, **kwargs) -> 'Flow':
        self._build_graph()
        if backend in {'thread', 'process'}:
            self._service_contexts.clear()
            for v in self._service_nodes.values():
                v['parsed_args'].parallel_backend = backend
                s = self._service2builder[v['service']](v['parsed_args'])
                self._service_contexts.append(s)
        else:
            raise NotImplementedError('backend=%s is not supported yet' % backend)
        self._build_level = Flow.BuildLevel.RUNTIME
        return self

    def __call__(self, *args, **kwargs):
        return self.build(*args, **kwargs)

    def __enter__(self):
        if self._build_level.value < Flow.BuildLevel.RUNTIME.value:
            self.logger.warning(
                'current build_level=%s, lower than required. '
                'build the flow now via build() with default parameters' % self._build_level)
            self.build()
        self._service_stack = ExitStack()
        for k in self._service_contexts:
            self._service_stack.enter_context(k)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, '_service_stack'):
            self._service_stack.close()

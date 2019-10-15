from functools import wraps

from ..cli.parser import set_router_parser, set_indexer_parser, \
    set_frontend_parser, set_preprocessor_parser, \
    set_encoder_parser
from ..service.base import BetterEnum, ServiceManager
from ..service.encoder import EncoderService
from ..service.frontend import FrontendService
from ..service.indexer import IndexerService
from ..service.preprocessor import PreprocessorService
from ..service.router import RouterService


class BuildLevel(BetterEnum):
    EMPTY = 0
    GRAPH = 1
    RUNTIME = 2


class Service(BetterEnum):
    Frontend = 0
    Encoder = 1
    Router = 2
    Indexer = 3
    Preprocessor = 4


class FlowIncompleteError(ValueError):
    """Exception when the flow missing some important component to run"""


class FlowTopologyError(ValueError):
    """Exception when the topology is ambiguous"""


class FlowMissingNode(ValueError):
    """Exception when the topology is ambiguous"""


class FlowBuildLevelMismatch(ValueError):
    """Exception when required level is higher than the current build level"""


def build_required(required_level: 'BuildLevel'):
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


service_map = {
    Service.Encoder: {
        'parser': set_encoder_parser,
        'builder': lambda x: ServiceManager(EncoderService, x),
        'cmd': 'encode'},
    Service.Router: {
        'parser': set_router_parser,
        'builder': lambda x: ServiceManager(RouterService, x),
        'cmd': 'route',
    },
    Service.Indexer: {
        'parser': set_indexer_parser,
        'builder': lambda x: ServiceManager(IndexerService, x),
        'cmd': 'index'
    },
    Service.Frontend: {
        'parser': set_frontend_parser,
        'builder': FrontendService,
        'cmd': 'frontend'
    },
    Service.Preprocessor: {
        'parser': set_preprocessor_parser,
        'builder': lambda x: ServiceManager(PreprocessorService, x),
        'cmd': 'preprocess'
    }
}

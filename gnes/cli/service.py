from .base import get_base_parser


def get_service_parser():
    parser = get_base_parser()
    parser.add_argument('--host', type=str, default='127.0.0.1',
                        help='the ip address of the host')
    parser.add_argument('--port_in', type=int, default=5555,
                        help='port for input data')
    parser.add_argument('--port_out', type=int, default=5556,
                        help='port for output data')
    parser.add_argument('--port_ctrl', type=int, default=5557,
                        help='port for control the service')
    return parser

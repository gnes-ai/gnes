
from gnes.helper import batch_iterator
from gnes.proto import gnes_pb2, gnes_pb2_grpc
from gnes.preprocessor.text import txt_file2pb_docs, line2pb_doc
from gnes.proto import send_message, recv_message
from gnes.service.base import BaseService
from gnes.service.base import SocketType


import uuid
from gnes.cli.parser import set_http_service_parser

data = open('query.txt').read().split('\n')

pd_d = [line2pb_doc(l) for l in data]

req = gnes_pb2.Request()
req.search.query = pd_d[0]
req.search.top_k = 10

args = set_http_service_parser().parse_args()
args.port_in = 8599
args.port_out = 8598
args.socket_out = SocketType.PUSH_CONNECT
args.socket_in = SocketType.SUB_CONNECT
args.identity = '1'

print(args)
with BaseService(args, use_event_loop=False) as bs:
    msg = gnes_pb2.Message()
    msg.envelope.client_id = bs.identity
    if req.request_id:
        msg.envelope.request_id = req.request_id
    else:
        msg.envelope.request_id = str(uuid.uuid4())
        print('request_id is missing, filled it with a random uuid!')
    msg.envelope.part_id = 1
    msg.envelope.num_part = 1
    msg.envelope.timeout = 5000
    r = msg.envelope.routes.add()
    r.service = bs.__class__.__name__
    r.timestamp.GetCurrentTime()
    msg.request.CopyFrom(req)

    send_message(bs.out_sock, msg, args.timeout)
    resp = recv_message(bs.in_sock, args.timeout)
    print(resp)

from gnes.client.base import ZmqClient
from gnes.cli.parser import set_service_parser
from gnes.service.base import SocketType
from gnes.proto import gnes_pb2
from gnes.proto import array2blob
import numpy as np


port_a = 1121
port_b = 1122

args = set_service_parser().parse_args(
    ['--port_in',str(port_a),
     '--port_out', str(port_b),
     '--socket_in', str(SocketType.PULL_CONNECT),
     '--socket_out', str(SocketType.PUSH_CONNECT),])

client = ZmqClient(args)

msg = gnes_pb2.Message()
# train index
docs = msg.request.train.docs


doc_list = [np.random.randint(0, 255, [2, 2, 5, 5, 3]).astype(np.int8)
            for _ in range(1)]


def fake_video_doc_gen(msg, doc_list):
    for doc in doc_list:
        d = msg.request.index.docs.add()
        d.doc_type = gnes_pb2.Document.VIDEO
        for _ in range(len(doc)):
            c = d.chunks.add()
            c.blob.CopyFrom(array2blob(doc[_]))
    return msg

# query: msg.request.search.query
msg = fake_video_doc_gen(msg, doc_list)
client.send_message(msg)
client.recv_message(timeout=100)

import grpc

from ..proto import gnes_pb2_grpc
from ..proto.request.text.base import TextRequestGenerator


class CLIClient:
    def __init__(self, args):
        all_docs = [v.strip() for v in args.txt_file]
        text_req_gen = TextRequestGenerator()

        with grpc.insecure_channel(
                '%s:%s' % (args.grpc_host, args.grpc_port),
                options=[('grpc.max_send_message_length', 50 * 1024 * 1024),
                         ('grpc.max_receive_message_length', 50 * 1024 * 1024)]) as channel:
            stub = gnes_pb2_grpc.GnesRPCStub(channel)

            if args.mode == 'train':
                for req in text_req_gen.train(all_docs, args.batch_size):
                    resp = stub._Call(req)
                    print(resp)
            elif args.mode == 'index':
                for req in text_req_gen.index(all_docs, args.batch_size):
                    resp = stub._Call(req)
                    print(resp)
            elif args.mode == 'query':
                for idx, q in enumerate(all_docs):
                    for req in text_req_gen.query(q, args.top_k):
                        resp = stub._Call(req)
                        print(resp)
                        print('query %d result: %s' % (idx, resp))
                        input('press any key to continue...')

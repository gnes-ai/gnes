import zipfile

import grpc

from ..proto import gnes_pb2_grpc, RequestGenerator


class CLIClient:
    def __init__(self, args):
        if args.data_type == 'text':
            all_bytes = [v.encode() for v in args.txt_file]
        elif args.data_type == 'image':
            zipfile_ = zipfile.ZipFile(args.image_zip_file, "r")
            all_bytes = [zipfile_.open(v).read() for v in zipfile_.namelist()]
        elif args.data_type == 'video':
            raise NotImplementedError
        else:
            raise ValueError(
                '--data_type can only be text, image or video')

        with grpc.insecure_channel(
                '%s:%s' % (args.grpc_host, args.grpc_port),
                options=[('grpc.max_send_message_length', 70 * 1024 * 1024),
                         ('grpc.max_receive_message_length', 70 * 1024 * 1024)]) as channel:
            stub = gnes_pb2_grpc.GnesRPCStub(channel)

            if args.mode == 'train':
                for req in RequestGenerator.train(all_bytes, args.batch_size):
                    resp = stub._Call(req)
                    print(resp)
            elif args.mode == 'index':
                for req in RequestGenerator.index(all_bytes, args.batch_size):
                    resp = stub._Call(req)
                    print(resp)
            elif args.mode == 'query':
                for idx, q in enumerate(all_bytes):
                    for req in RequestGenerator.query(q, args.top_k):
                        resp = stub._Call(req)
                        print(resp)
                        print('query %d result: %s' % (idx, resp))
                        input('press any key to continue...')

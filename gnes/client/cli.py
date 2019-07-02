import grpc
import zipfile
from PIL import Image

from ..proto import gnes_pb2_grpc
from ..proto.request.text.simple import TextRequestGenerator
from ..proto.request.image.simple import ImageRequestGenerator


TARGET_IMG_SIZE = 224


class CLIClient:
    def __init__(self, args):
        all_docs = None
        req_gen = None
        if args.data_type == 'text':
            all_docs = [v.strip() for v in args.txt_file]
            req_gen = TextRequestGenerator()
        elif args.data_type == 'image':
            all_docs = []
            zipfile_ = zipfile.ZipFile(args.image_folder, "r")
            for img_file in zipfile_.namelist():
                image = Image.open(zipfile_.open(img_file, 'r')).resize((TARGET_IMG_SIZE, TARGET_IMG_SIZE))
                all_docs.append(image)
            req_gen = ImageRequestGenerator()
        elif args.data_type == 'video':
            pass
        else:
            raise ValueError(
                '--data_type can only be text, image or video')

        with grpc.insecure_channel(
                '%s:%s' % (args.grpc_host, args.grpc_port),
                options=[('grpc.max_send_message_length', 70 * 1024 * 1024),
                         ('grpc.max_receive_message_length', 70 * 1024 * 1024)]) as channel:
            stub = gnes_pb2_grpc.GnesRPCStub(channel)

            if all_docs and req_gen:
                if args.mode == 'train':
                    for req in req_gen.train(all_docs, args.batch_size):
                        resp = stub._Call(req)
                        print(resp)
                elif args.mode == 'index':
                    for req in req_gen.index(all_docs, args.batch_size):
                        resp = stub._Call(req)
                        print(resp)
                elif args.mode == 'query':
                    for idx, q in enumerate(all_docs):
                        for req in req_gen.query(q, args.top_k):
                            resp = stub._Call(req)
                            print(resp)
                            print('query %d result: %s' % (idx, resp))
                            input('press any key to continue...')
            else:
                raise ValueError(
                    '--do not support videos now'
                )

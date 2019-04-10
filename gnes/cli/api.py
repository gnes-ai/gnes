def encode(args):
    from ..service import EncoderService
    with EncoderService(args) as es:
        es.join()


def index(args):
    from ..service import IndexerService
    with IndexerService(args) as es:
        es.join()


def search(args):
    from ..module import GNES
    with GNES.load(args.config) as gnes:
        if args.interactive:
            while True:
                for r in gnes.query([input('query: ')], top_k=10)[0]:
                    print(r)
        else:
            print(gnes.query([args.query], top_k=10))


def client(args):
    from ..service import ClientService

    with ClientService(args) as cs:
        data = [v for v in args.txt_file if v.strip()]
        if not data:
            raise ValueError('input text file is empty, nothing to do')
        else:
            result = cs.query(data)
            if result:
                print(type(result))
                print(result.client_id)
                print(result.req_id)
                print(result.content_type)
                print(result.msg_type)
                print(type(result.msg_content))
        cs.join()

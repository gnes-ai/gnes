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

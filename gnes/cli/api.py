def encode(args):
    from ..service import EncoderService
    with EncoderService(args) as es:
        es.join()


def index(args):
    from ..module import GNES
    from ..document import UniSentDocument
    import glob

    with GNES.load_yaml(args.config) as gnes:
        for f in glob.glob(args.document):
            docs = UniSentDocument.from_file(f)
            gnes.train(docs)
            gnes.add(docs)
        gnes.dump()


def search(args):
    from ..module import GNES
    with GNES.load(args.config) as gnes:
        if args.interactive:
            while True:
                for r in gnes.query([input('query: ')], top_k=10)[0]:
                    print(r)
        else:
            print(gnes.query([args.query], top_k=10))

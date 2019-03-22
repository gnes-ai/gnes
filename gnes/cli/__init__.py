from .parser import get_run_args

__all__ = []


def main():
    args = get_run_args()
    globals().get(args.cli)(args)


def index(args):
    from ..module import GNES
    from gnes.document import UniSentDocument
    import glob

    with GNES.load_yaml(args.config) as gnes:
        for f in glob.glob(args.document):
            gnes.train(UniSentDocument.from_file(f))
            gnes.add(UniSentDocument.from_file(f))
        gnes.dump()


def search(args):
    from ..module import GNES
    with GNES.load(args.config) as gnes:
        if args.interactive:
            while True:
                print(gnes.query([input('query: ')], top_k=10))
        else:
            print(gnes.query([args.query], top_k=10))

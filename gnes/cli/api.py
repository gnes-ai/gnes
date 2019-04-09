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
    from ..client import BaseClient
    from ..service import ServiceMode

    with BaseClient(args.host_in, args.host_out, args.port_in, args.port_out, timeout=args.timeout) as bc:
        data = [v for v in args.txt_file if v.strip()]
        if not data:
            raise ValueError('input text file is empty, nothing to do')
        else:
            if args.mode == ServiceMode.QUERY:
                print(bc.send_receive(data))
            else:
                bc.send(data)

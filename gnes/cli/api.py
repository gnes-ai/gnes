def encode(args):
    from ..service.encoder import EncoderService
    with EncoderService(args) as es:
        es.join()


def index(args):
    from ..service.indexer import IndexerService
    with IndexerService(args) as es:
        es.join()


def proxy(args):
    from ..service import proxy as my_proxy
    if not args.proxy_type:
        raise ValueError('--proxy_type is required when starting a proxy from CLI')
    with getattr(my_proxy, args.proxy_type)(args) as es:
        es.join()


def client(args):
    from ..service.client import ClientService
    from zmq.utils import jsonapi
    with ClientService(args) as cs:
        data = [v for v in args.txt_file if v.strip()]
        if not data:
            raise ValueError('input text file is empty, nothing to do')
        else:
            result = cs.query(data)
            if result:
                print(result.client_id)
                print(result.req_id)
                print(result.content_type)
                print(result.msg_type)
                for _ in jsonapi.loads(result.msg_content):
                    print(_)
        cs.join()

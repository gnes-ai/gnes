from .parser import get_run_args

__all__ = []


def main():
    args = get_run_args()
    if args: run(args)


def run(args):
    from ..module import GNES
    g = GNES.load_yaml(args.config)  # type: 'GNES'
    g.dump()

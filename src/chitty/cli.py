import functools
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace

import trio
from . import debug, server


def parse_args() -> Namespace:
    parser_kw = {'formatter_class': ArgumentDefaultsHelpFormatter}
    parser = ArgumentParser(description='Chitty char server management')
    subparsers = parser.add_subparsers(help='Available commands')
    run_parser = subparsers.add_parser('run', help='Launch the server', **parser_kw)
    run_parser.add_argument(
        '-H', '--host', default='127.0.0.1', help='IP address to bind tos'
    )
    run_parser.add_argument(
        '-p', '--port', type=int, default=5000, help='port number to bind to'
    )
    run_parser.add_argument(
        '-i', '--instrument',
        help='[optional] name of instrumentation class from debug module',
    )
    return parser.parse_args()


def run() -> None:
    opts = parse_args()
    kw = {}
    if opts.instrument:
        instrument_cls = getattr(debug, opts.instrument, None)
        if instrument_cls is None:
            print(f'Instrumentation class {opts.instrument} not found')
        else:
            print(f'Running with instrumentation {opts.instrument}')
            kw['instruments'] = [instrument_cls()]
    entrypoint = functools.partial(server.main, host=opts.host, port=opts.port)
    try:
        trio.run(entrypoint, **kw)
    except KeyboardInterrupt:
        print()

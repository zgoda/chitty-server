import functools
from argparse import ArgumentParser, Namespace

import trio

from . import server


def parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument('-H', '--host', default='127.0.0.1')
    parser.add_argument('-p', '--port', type=int, default=5000)
    return parser.parse_args()


def run() -> None:
    opts = parse_args()
    entrypoint = functools.partial(server.main, host=opts.host, port=opts.port)
    trio.run(entrypoint)

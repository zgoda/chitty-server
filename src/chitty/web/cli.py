from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace

from dotenv import find_dotenv, load_dotenv
from werkzeug import run_simple


def parse_args() -> Namespace:
    parser_kw = {"formatter_class": ArgumentDefaultsHelpFormatter}
    parser = ArgumentParser(description="Chitty auxiliary web service")
    subparsers = parser.add_subparsers(help="Available commands")
    run_parser = subparsers.add_parser("run", help="Launch the server", **parser_kw)
    run_parser.add_argument(
        "-H", "--host", default="127.0.0.1", help="IP address to bind to"
    )
    run_parser.add_argument(
        "-p", "--port", type=int, default=5001, help="port number to bind to"
    )
    return parser.parse_args()


def main():
    load_dotenv(find_dotenv())
    from .app import make_app

    application = make_app()
    opts = parse_args()
    run_simple(opts.host, opts.port, application, use_reloader=True)

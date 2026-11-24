"""Run a local, quiet WSGI server. Use gunicorn behind TLS in production."""
import argparse
from pathlib import Path
import sys
from wsgiref.simple_server import WSGIRequestHandler, make_server

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.messenger import create_app


class QuietHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8503)
    args = parser.parse_args()
    with make_server(args.host, args.port, create_app(), handler_class=QuietHandler) as server:
        print(f'CipherCraft messenger listening on {args.host}:{args.port}')
        server.serve_forever()

import os

from falcon import Request, Response


class ServerMetadataResource:

    def on_get(self, req: Request, resp: Response) -> None:
        resp.media = {
            'chat': {
                'host': os.getenv('CHITTY_CHAT_HOST', '127.0.0.1'),
                'port': int(os.getenv('CHITTY_CHAT_PORT', '5000'))
            }
        }

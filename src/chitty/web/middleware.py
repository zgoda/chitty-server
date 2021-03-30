from typing import Any

from falcon import Request, Response


class CORSMiddleware:
    """Extremely simple CORS middleware that allows everything from
    everywhere.

    Do not use except for development.
    """

    def process_response(
                self, req: Request, resp: Response, resource: Any, req_succeeded: bool
            ) -> None:
        resp.set_header('Access-Control-Allow-Origin', '*')

        if (
                    req_succeeded
                    and req.method == 'OPTIONS'
                    and req.get_header('Access-Control-Request-Method')
                ):
            allow = resp.get_header('Allow')
            resp.delete_header('Allow')
            allow_headers = req.get_header(
                'Access-Control-Request-Headers',
                default='*'
            )
            resp.set_headers((
                ('Access-Control-Allow-Methods', allow),
                ('Access-Control-Allow-Headers', allow_headers),
                ('Access-Control-Max-Age', '86400'),
            ))


cors = CORSMiddleware()

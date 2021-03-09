import json

from trio_websocket import ConnectionClosed, WebSocketRequest, serve_websocket

from .controller import route_message


async def server(request: WebSocketRequest) -> None:
    ws = await request.accept()
    while True:
        try:
            message = await ws.get_message()
            try:
                payload = json.loads(message)
            except json.decoder.JSONDecodeError:
                await ws.send_message('Invalid message, expected: object')
            else:
                route_message(payload)
        except ConnectionClosed:
            break


async def main(*, host: str, port: int) -> None:
    await serve_websocket(server, host=host, port=port, ssl_context=None)

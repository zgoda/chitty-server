import json

from trio_websocket import ConnectionClosed, WebSocketRequest, serve_websocket

from . import errors
from .controller import route_message
from .user import registry
from .utils import error_response

MAX_MESSAGE_SIZE = 2 ** 16  # 64 KB
MESSAGE_QUEUE_SIZE = 4


async def server(request: WebSocketRequest) -> None:
    """Connection handler.

    This function will be run for any incoming connection.

    :param request: websocket request object
    :type request: WebSocketRequest
    """
    ws = await request.accept()
    client = str(request.remote)
    while True:
        try:
            message = await ws.get_message()
            try:
                payload = json.loads(message)
            except json.decoder.JSONDecodeError:
                payload = error_response(
                    errors.E_REASON_MALFORMED,
                    message='Invalid message, expected: object',
                )
                await ws.send_message(json.dumps(payload))
            else:
                resp = await route_message(client, payload)
                if resp:
                    await ws.send_message(json.dumps(resp))
            user = registry.get(client_id=client)
            if user:
                topic, message = await user.collect_message()
                message['topic'] = topic
                await ws.send_message(json.dumps(message))
            print('end loop run')
        except ConnectionClosed:
            registry.remove(client_id=client)
            print(f'bye {client}')
            break


async def main(*, host: str, port: int) -> None:
    """Websocket server entrypoint.

    :param host: host name or IP address to bind to
    :type host: str
    :param port: TCP port
    :type port: int
    """
    await serve_websocket(
        server, host=host, port=port, ssl_context=None,
        max_message_size=MAX_MESSAGE_SIZE, message_queue_size=MESSAGE_QUEUE_SIZE,
    )

import json
import trio

from trio_websocket import (
    ConnectionClosed, WebSocketConnection, WebSocketRequest, serve_websocket,
)

from . import errors
from .controller import route_message
from .user import registry
from .utils import error_response

MAX_MESSAGE_SIZE = 2 ** 16  # 64 KB
MESSAGE_QUEUE_SIZE = 4


async def ws_message_processor(ws: WebSocketConnection, client: str) -> None:
    """Task that reads and routes messages from WebSocket connection.

    :param ws: WebSocket connection object
    :type ws: WebSocketConnection
    :param client: client ID from request
    :type client: str
    """
    while True:
        await trio.sleep(0)
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
        except ConnectionClosed:
            registry.remove(client_id=client)
            break


async def chat_message_processor(ws: WebSocketConnection, client: str) -> None:
    """Task that collects messages from chat topic and sends them to WebSocket
    client.

    :param ws: WebSocket connection object
    :type ws: WebSocketConnection
    :param client: client ID from request
    :type client: str
    """
    while True:
        await trio.sleep(0)
        if ws.closed:
            registry.remove(client_id=client)
            break
        user = registry.get(client_id=client)
        if user:
            message = await user.collect_message()
            payload = message.message
            payload['topic'] = message.topic
            try:
                await ws.send_message(json.dumps(payload))
            except ConnectionClosed:
                registry.remove(client_id=client)
                break


async def server(request: WebSocketRequest) -> None:
    """Connection handler.

    This function will be run for any incoming connection.

    :param request: websocket request object
    :type request: WebSocketRequest
    """
    ws = await request.accept()
    client = str(request.remote)
    async with trio.open_nursery() as nursery:
        nursery.start_soon(ws_message_processor, ws, client)
        nursery.start_soon(chat_message_processor, ws, client)


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

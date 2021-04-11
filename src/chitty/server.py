import json
import logging
import os

import trio
from trio_websocket import (
    ConnectionClosed, WebSocketConnection, WebSocketRequest, serve_websocket,
)

from . import errors
from .controller import route_message
from .user import registry
from .utils import error_response

MAX_CLIENTS = int(os.getenv('WS_MAX_CLIENTS', '16'))

MAX_MESSAGE_SIZE = 2 ** 16  # 64 KB
MESSAGE_QUEUE_SIZE = 4

log = logging.getLogger(__name__)

STATS = {
    'num_clients': 0,
}


def _post_close_cleanup(client: str):
    registry.remove(client_id=client)
    STATS['num_clients'] -= 1
    logging.warning(f'client connection for {client} closed')


async def ws_message_processor(ws: WebSocketConnection, client: str) -> None:
    """Task that reads and routes messages from WebSocket connection.

    :param ws: WebSocket connection object
    :type ws: WebSocketConnection
    :param client: client ID from request
    :type client: str
    """
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
                log.exception('malformed message')
                await ws.send_message(json.dumps(payload))
            else:
                try:
                    resp = await route_message(client, payload)
                    log.debug('message processed')
                    if resp:
                        await ws.send_message(json.dumps(resp))
                except errors.ChatMessageException as e:
                    payload = error_response(
                        errors.E_REASON_TYPE_INVALID, message=str(e)
                    )
                    log.exception('message routing error')
                    await ws.send_message(json.dumps(payload))
        except ConnectionClosed:
            _post_close_cleanup(client)
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
        if ws.closed:
            _post_close_cleanup(client)
            break
        user = registry.get(client_id=client)
        if user:
            async for message in user.message_stream():
                try:
                    await message.send(ws)
                    log.debug('message sent')
                except ConnectionClosed:
                    _post_close_cleanup(client)
                    break
        else:
            await trio.sleep(0.2)


async def server(request: WebSocketRequest) -> None:
    """Connection handler.

    This function will be run for any incoming connection. Request is accepted
    unless number of open connections exceeds ``MAX_CLIENTS``, rejection comes
    with code 403.

    :param request: websocket request object
    :type request: WebSocketRequest
    """
    client = str(request.remote)
    if STATS['num_clients'] >= MAX_CLIENTS:
        await request.reject(503)
        log.warning(
            f'Maximum number of clients reached, request from {client} rejected'
        )
        return
    if len(request.path) < 2:
        await request.reject(401, body='Please authenticate first'.encode('utf-8'))
        log.warning(f'Client {client} not authenticated')
        return
    ws = await request.accept()
    STATS['num_clients'] += 1
    log.debug(f'connection from {client} accepted')
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
    logging.basicConfig(level=os.getenv('CHITTY_LOGLEVEL', 'INFO'))
    log.info(f'starting on {host}:{port}')
    await serve_websocket(
        server, host=host, port=port, ssl_context=None,
        max_message_size=MAX_MESSAGE_SIZE, message_queue_size=MESSAGE_QUEUE_SIZE,
    )

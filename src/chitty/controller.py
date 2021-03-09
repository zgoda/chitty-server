from typing import Mapping, Union

from .handlers import register_user

MSG_TYPE_REGISTER = 'reg'
MSG_TYPE_CREATE_TOPIC = 'topic'
MSG_TYPE_JOIN_PRIVATE_TOPIC = 'join'
MSG_TYPE_ACCEPT_JOIN_PRIVATE_TOPIC = 'accept'
MSG_TYPE_DIRECT_MESSAGE = 'dm'
MSG_TYPE_MESSAGE = 'msg'

KNOWN_MSG_TYPES = [
    MSG_TYPE_REGISTER,
    MSG_TYPE_CREATE_TOPIC,
    MSG_TYPE_JOIN_PRIVATE_TOPIC,
    MSG_TYPE_ACCEPT_JOIN_PRIVATE_TOPIC,
    MSG_TYPE_DIRECT_MESSAGE,
    MSG_TYPE_MESSAGE,
]

MSG_FIELDS = {
    MSG_TYPE_REGISTER: ['value'],
    MSG_TYPE_CREATE_TOPIC: ['value'],
    MSG_TYPE_JOIN_PRIVATE_TOPIC: ['value'],
    MSG_TYPE_ACCEPT_JOIN_PRIVATE_TOPIC: ['to', 'value'],
    MSG_TYPE_DIRECT_MESSAGE: ['to', 'value'],
    MSG_TYPE_MESSAGE: ['to', 'value'],
}

MSG_HANDLERS = {
    MSG_TYPE_REGISTER: register_user
}


class ChatMessageException(Exception):
    pass


class MessageRoutingError(ChatMessageException):
    pass


class MessageFormatError(ChatMessageException):
    pass


def validate_message(msg_type: str, message: Mapping[str, Union[str, int]]) -> bool:
    return set(message.keys()).issuperset(MSG_FIELDS[msg_type])


async def route_message(client: str, msg: Mapping[str, Union[str, int]]) -> None:
    msg_type = msg.pop('type', None)
    if not msg_type or msg_type not in KNOWN_MSG_TYPES:
        raise MessageRoutingError('Unknown message type')
    if not validate_message(msg_type, msg):
        raise MessageFormatError('Invalid message format')
    handler = MSG_HANDLERS[msg_type]
    await handler(client, **msg)

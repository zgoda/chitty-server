from typing import Mapping, Optional, Union

from . import handlers
from .errors import MessageFormatError, MessageRoutingError
from .message import (
    KNOWN_MSG_TYPES, MSG_FIELDS, MSG_TYPE_DIRECT_MESSAGE, MSG_TYPE_MESSAGE,
    MSG_TYPE_REGISTER, MSG_TYPE_SUBSCRIBE_TOPIC,
)

MSG_HANDLERS = {
    MSG_TYPE_REGISTER: handlers.register_user,
    MSG_TYPE_MESSAGE: handlers.post_message,
    MSG_TYPE_SUBSCRIBE_TOPIC: handlers.subscribe,
    MSG_TYPE_DIRECT_MESSAGE: handlers.direct_message,
}


def validate_message(msg_type: str, message: Mapping[str, Union[str, int]]) -> bool:
    """Validate message structure.

    :param msg_type: type of message
    :type msg_type: str
    :param message: message contents
    :type message: Mapping[str, Union[str, int]]
    :return: validation result
    :rtype: bool
    """
    return set(message.keys()).issuperset(MSG_FIELDS[msg_type])


async def route_message(
            client: str, msg: Mapping[str, Union[str, int]]
        ) -> Optional[dict]:
    """Validate and route message to appropriate handler.

    :param client: client ID
    :type client: str
    :param msg: received message
    :type msg: Mapping[str, Union[str, int]]
    :raises MessageRoutingError: if message is of unknown type
    :raises MessageFormatError: if message fields do not match spec
    :return: whatever handler produces
    :rtype: Optional[dict]
    """
    msg_type = msg.pop('type', None)
    if not msg_type or msg_type not in KNOWN_MSG_TYPES:
        raise MessageRoutingError('Unknown message type')
    if not validate_message(msg_type, msg):
        raise MessageFormatError('Invalid message format')
    handler = MSG_HANDLERS[msg_type]
    return await handler(client, **msg)

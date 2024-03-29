from typing import Mapping, MutableMapping, Optional, Union

from . import handlers
from .errors import MessageFormatError, MessageRoutingError
from .message import (
    KNOWN_MSG_TYPES,
    MSG_FIELDS,
    MSG_TYPE_DIRECT_MESSAGE,
    MSG_TYPE_MESSAGE,
    MSG_TYPE_REPLY,
    MSG_TYPE_SUBSCRIBE_TOPIC,
)
from .user import User

MSG_HANDLERS = {
    MSG_TYPE_MESSAGE: handlers.post_message,
    MSG_TYPE_REPLY: handlers.post_reply_message,
    MSG_TYPE_SUBSCRIBE_TOPIC: handlers.subscribe,
    MSG_TYPE_DIRECT_MESSAGE: handlers.direct_message,
}


def validate_message(
    msg_type: str, message: Mapping[str, Union[str, int, float]]
) -> bool:
    """Validate message structure.

    This function returns False if message is missing any required field,
    True otherwise.

    :param msg_type: type of message
    :type msg_type: str
    :param message: message contents
    :type message: Mapping[str, Union[str, int, float]]
    :return: validation result
    :rtype: bool
    """
    return set(message.keys()).issuperset(MSG_FIELDS[msg_type])  # type: ignore


def normalise_message_fields(message: MutableMapping[str, str | int]) -> None:
    """Make message fields "Python friendly" from "JS friendly".

    This is required to use message data as keyword param in
    :class:`~chitty.message.Message` constructor.

    This function changes message structure in place.

    :param message: message structure
    :type message: MutableMapping[str, str | int]
    """
    invalid = {"replyingTo"}
    subst = {
        "replyingTo": "replying_to",
    }
    to_subst = set(message.keys()).intersection(invalid)
    for key in to_subst:
        new_key = subst[key]
        message[new_key] = message[key]
        del message[key]


async def route_message(
    user: User, msg: MutableMapping[str, Union[str, int]]
) -> Optional[dict]:
    """Validate and route message to appropriate handler.

    :param client: client ID
    :type client: str
    :param msg: received message
    :type msg: MutableMapping[str, Union[str, int]]
    :raises MessageRoutingError: if message is of unknown type
    :raises MessageFormatError: if message fields do not match spec
    :return: whatever handler produces
    :rtype: Optional[dict]
    """
    msg_type = msg.pop("type", None)
    if not msg_type or msg_type not in KNOWN_MSG_TYPES:
        raise MessageRoutingError("Unknown message type")
    if not validate_message(msg_type, msg):
        raise MessageFormatError("Invalid message format")
    normalise_message_fields(msg)
    handler = MSG_HANDLERS[msg_type]
    return await handler(user, **msg)

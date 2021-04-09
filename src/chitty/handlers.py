"""Message handlers implementation.

Handler is (async) function that takes client identifier and any keyword
arguments required by message spec. Anything that is returned from this
function will be serialised and then sent back to client as response.
"""

import logging
from typing import Mapping, Optional

import nanoid
import trio

from . import errors, topic, utils
from .message import MSG_TYPE_REGISTER, MSG_TYPE_SUBSCRIBE_TOPIC, make_message
from .user import User, registry

log = logging.getLogger(__name__)


async def register_user(client: str, *, value: str, **kw) -> Mapping[str, str]:
    """Register client instance as both client (the agent) and user.

    This function returns user data structure. If key is not provided it will
    be generated.

    :param client: client ID
    :type client: str
    :param value: user name/handle
    :type value: str
    :return: user data
    :rtype: Mapping[str, str]
    """
    key = kw.pop('key', nanoid.generate())
    user = User(name=value, client_id=client, key=key)
    registry.add(user)
    payload = user.to_map(with_topics=True)
    payload['type'] = MSG_TYPE_REGISTER
    log.debug(f'user {value} registered')
    return payload


async def post_message(client: str, *, to: str, value: str) -> Optional[dict]:
    """Post chat message on specific topic.

    This function return None if operation succeeds, error structure
    otherwise.

    :param client: client ID
    :type client: str
    :param to: topic name
    :type to: str
    :param value: message text
    :type value: str
    :return: optional error structure
    :rtype: Optional[dict]
    """
    user = registry.get(client_id=client)
    if not user:
        log.warning(f'client from space: {client}')
        return utils.error_response(errors.E_REASON_NOTREG)
    if to in topic.SYSTEM_TOPICS:
        log.warning(f'client {client} tries to post to system topic')
        return utils.error_response(
            errors.E_REASON_TOPIC_SYSTEM,
            message=f'Topic {to} is not available for posting',
        )
    await user.post_message(to, value)
    log.debug(f'{client} posted message to {to}')


async def post_reply_message(
            client: str, *, to: str, value: str, replying_to: Mapping[str, str]
        ) -> Optional[dict]:
    ret = await post_message(client, to=to, value=value)
    in_reply_to = replying_to['key']
    log.debug(f'{client} posted reply message to {in_reply_to} in {to}')
    return ret


async def subscribe(client: str, *, value: str) -> Optional[dict]:
    """Subscribe user to specified topic.

    :param client: client ID
    :type client: str
    :param value: topic name
    :type value: str
    :return: optional error structure
    :rtype: Optional[dict]
    """
    user = registry.get(client_id=client)
    if not user:
        log.warning(f'client from space: {client}')
        return utils.error_response(errors.E_REASON_NOTREG)
    user.subscribe(value)
    await trio.sleep(0)
    payload = user.to_map(with_topics=True)
    payload['type'] = MSG_TYPE_SUBSCRIBE_TOPIC
    log.debug(f'{client} subscribed to {value}')
    return payload


async def direct_message(client: str, *, to: str, value: str) -> None:
    """Send direct message to another user.

    :param client: client ID
    :type client: str
    :param to: recipient user ID (key)
    :type to: str
    :param value: message
    :type value: str
    """
    sender = registry.get(client_id=client)
    if not sender:
        log.warning(f'client from space: {client}')
        return utils.error_response(errors.E_REASON_NOTREG)
    recipient = registry.get(key=to)
    if not recipient:
        log.warning(f'recipient {to} not found')
        return utils.error_response(
            errors.E_REASON_NOTREG, message='Recipient not found'
        )
    message = make_message(user_data=sender.to_map(), topic=recipient.key, msg=value)
    await message.publish()
    log.debug(f'direct message from {client} to {to} sent')

"""Message handlers implementation.

Handler is (async) function that takes client identifier and any keyword
arguments required by message spec. Anything that is returned from this
function will be serialised and then sent back to client as response.
"""

import logging
from typing import Mapping, Optional

import trio

from . import errors, topic, utils
from .event import SYS_USER_DATA
from .message import MSG_TYPE_SUBSCRIBE_TOPIC, make_message
from .user import User, registry

log = logging.getLogger(__name__)


async def post_message(user: User, *, to: str, value: str) -> Optional[dict]:
    """Post chat message on specific topic.

    This function return None if operation succeeds, error structure
    otherwise.

    :param user: user object
    :type client: User
    :param to: topic name
    :type to: str
    :param value: message text
    :type value: str
    :return: optional error structure
    :rtype: Optional[dict]
    """
    if to in topic.SYSTEM_TOPICS:
        log.warning(f'user {user.name} tries to post to system topic')
        return utils.error_response(
            errors.E_REASON_TOPIC_SYSTEM,
            message=f'Topic {to} is not available for posting',
        )
    await user.post_message(to, value)
    log.debug(f'{user.name} posted message to {to}')


async def post_reply_message(
            user: User, *, to: str, value: str, replying_to: Mapping[str, str]
        ) -> Optional[dict]:
    """Post reply message.

    :param user: sender user object
    :type user: User
    :param to: topic name
    :type to: str
    :param value: message string
    :type value: str
    :param replying_to: reply recipient data
    :type replying_to: Mapping[str, str]
    :return: optonal error response from message posting
    :rtype: Optional[dict]
    """
    ret = await post_message(user, to=to, value=value)
    if ret:
        return ret
    in_reply_to = replying_to['name']
    msg = make_message(
        user_data=SYS_USER_DATA, topic=in_reply_to, msg="You've got reply"
    )
    await msg.publish()


async def subscribe(user: User, *, value: str) -> dict:
    """Subscribe user to specified topic.

    :param client: client ID
    :type client: str
    :param value: topic name
    :type value: str
    :return: subscription confirmation message structure
    :rtype: dict
    """
    user.subscribe(value)
    await trio.sleep(0)
    payload = user.to_map(with_topics=True)
    payload['type'] = MSG_TYPE_SUBSCRIBE_TOPIC
    log.debug(f'{user.name} subscribed to {value}')
    return payload


async def direct_message(user: User, *, to: str, value: str) -> Optional[dict]:
    """Send direct message to another user.

    :param user: sender object
    :type user: User
    :param to: recipient name
    :type to: str
    :param value: message
    :type value: str
    :return: optional error structure
    :rtype: Optional[dict]
    """
    recipient = registry.get(to)
    if not recipient:
        log.warning(f'recipient {to} not found')
        return utils.error_response(
            errors.E_REASON_NOTREG, message='Recipient not found'
        )
    message = make_message(user_data=user.to_map(), topic=recipient.name, msg=value)
    await message.publish()
    log.debug(f'direct message from {user.name} to {recipient.name} sent')

"""Message handlers implementation.

Handler is (async) function that takes client identifier and any keyword
arguments required by message spec. Anything that is returned from this
function will be serialised and then sent back to client as response.
"""

from typing import Mapping, Optional

import nanoid

from . import utils, errors
from .user import User, registry


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
    return user.to_map()


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
        return utils.error_response(errors.E_REASON_NOTREG)
    await user.post_message(to, value)

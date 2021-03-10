"""Message handlers implementation.

Handler is (async) function that takes client identifier and any keyword
arguments required by message spec. Anything that is returned from this
function will be serialised and then sent back to client as response.
"""

import json
from typing import Mapping

import nanoid

from .storage import redis
from .user import User, registry


async def register_user(client: str, *, value: str) -> Mapping[str, str]:
    """Register client instance as both client (the agent) and user.

    This function also creates user events channel and subscribes it.

    :param client: client ID
    :type client: str
    :param value: user name/handle
    :type value: str
    :return: user data
    :rtype: Mapping[str, str]
    """
    user = User(name=value, client_id=client, key=nanoid.generate())
    clients = await redis().hget('clients', 'clients').autodecode
    clients = set(clients or [])
    clients.add((user.key, user.client_id, user.name))
    db = redis()
    db.hset('clients', {'clients': json.dumps(list(clients))})
    await db
    registry.add(user)
    return user.to_map()

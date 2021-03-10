import json

from .storage import redis


async def register_user(client: str, value: str) -> None:
    """Register client instance as both client (the agent) and user.

    :param client: client ID
    :type client: str
    :param value: user name/handle
    :type value: str
    """
    clients = await redis().hget('clients', 'clients').autodecode
    clients = set(clients or [])
    clients.add(client)
    users = await redis().hget('clients', 'users').autodecode
    users = set(users or [])
    users.add(value)
    db = redis()
    db.hset('clients', {'clients': json.dumps(list(clients))})
    db.hset('clients', {'users': json.dumps(list(users))})
    await db

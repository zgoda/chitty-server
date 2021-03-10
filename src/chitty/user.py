from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import List, Mapping, Optional

from redio.pubsub import PubSub

from .storage import redis


@dataclass
class User:
    name: str
    client_id: str
    key: str

    _pubsub: Optional[PubSub] = field(init=False, repr=False, default=None)
    _events: Optional[str] = field(init=False, repr=False, default=None)
    _subs: List[str] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        self._pubsub = redis.pubsub(self.client_id).autodecode.with_channel
        self._events = self._pubsub.subscribe(self.key)

    @classmethod
    def from_map(cls, data: Mapping[str, str]) -> User:
        return cls(**data)

    def to_map(self):
        return {
            'key': self.key,
            'client_id': self.client_id,
            'name': self.name,
        }

    async def post_message(self, topic: str, message: str) -> None:
        payload = {
            'date': time.time(),
            'from': self.to_map(),
            'message': message,
        }
        await redis().publish(topic, json.dumps(payload))


class UserRegistry:

    def __init__(self):
        self._users_by_client = {}
        self._users_by_key = {}

    def add(self, user: User):
        self._users_by_client[user.client_id] = user
        self._users_by_key[user.key] = user

    def get(
                self, *, client_id: Optional[str] = None, key: Optional[str] = None
            ) -> Optional[User]:
        if not any([client_id, key]):
            raise RuntimeError('Either client_id or key must be provided')
        if key:
            selector = key
            users = self._users_by_key
        else:
            selector = client_id
            users = self._users_by_client
        return users.get(selector)

    def remove(
                self, *, client_id: Optional[str] = None, key: Optional[str] = None
            ) -> None:
        if not any([client_id, key]):
            raise RuntimeError('Either client_id or key must be provided')
        if key:
            user = self._users_by_key[key]
        else:
            user = self._users_by_client[client_id]
        self._users_by_key.pop(user.key, None)
        self._users_by_client.pop(user.client_id, None)


registry = UserRegistry()

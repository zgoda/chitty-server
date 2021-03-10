from __future__ import annotations

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

    @classmethod
    def from_map(cls, data: Mapping[str, str]) -> User:
        return cls(**data)

    def to_map(self):
        return {
            'key': self.key,
            'client_id': self.client_id,
            'name': self.name,
        }


class UserRegistry:

    def __init__(self):
        self._users_by_client = {}
        self._users_by_key = {}

    def add(self, user: User):
        serialized = user.to_map()
        self._users_by_client[user.client_id] = serialized
        self._users_by_key[user.key] = serialized

    def get(
                self, *, client_id: Optional[str] = None, key: Optional[str] = None
            ) -> User:
        if not any([client_id, key]):
            raise RuntimeError('Either client_id or key must be provided')
        if key:
            selector = key
            users = self._users_by_key
        else:
            selector = client_id
            users = self._users_by_client
        return users[selector]


registry = UserRegistry()

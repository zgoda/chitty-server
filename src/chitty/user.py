from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Mapping, Optional

from redio.pubsub import PubSub

from .message import Message
from .storage import redis
from .topic import DEFAULT_TOPICS


@dataclass
class User:
    """User object structure.

    Upon object creation user will be subscribed to private topic and general
    chat.

    :ivar name: user screen name
    :type name: str
    :ivar client_id: WS client ID from request
    :type client_id: str
    :ivar key: user key
    :type key: str
    """

    name: str
    client_id: str
    key: str

    _pubsub: Optional[PubSub] = field(init=False, repr=False, default=None)

    def __post_init__(self):
        self._pubsub = redis.pubsub(self.key, *DEFAULT_TOPICS).autodecode.with_channel

    @classmethod
    def from_map(cls, data: Mapping[str, str]) -> User:
        """Deserialise user data into User object.

        :param data: serialised user data
        :type data: Mapping[str, str]
        :return: User instance
        :rtype: User
        """
        return cls(**data)

    def to_map(self) -> Mapping[str, str]:
        """Serialise User object into data dictionary.

        :return: serialised data
        :rtype: Mapping[str, str]
        """
        return {
            'key': self.key,
            'client_id': self.client_id,
            'name': self.name,
        }

    async def post_message(self, topic: str, message: str) -> None:
        """Post chat message to a topic.

        This also subscribes user to topic.

        :param topic: topic name
        :type topic: str
        :param message: message text
        :type message: str
        """
        self._pubsub.subscribe(topic)
        payload = {
            'date': time.time(),
            'from': self.to_map(),
            'message': message,
        }
        await redis().publish(topic, json.dumps(payload))

    async def collect_message(self) -> Message:
        """Fetch single message from subscribed topic pool.

        :return: topic name and message structure as named tuple
        :rtype: Message
        """
        topic, message = await self._pubsub
        return Message(topic, message)


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
            user = self._users_by_key.get(key)
        else:
            user = self._users_by_client.get(client_id)
        if user:
            self._users_by_key.pop(user.key, None)
            self._users_by_client.pop(user.client_id, None)


registry = UserRegistry()

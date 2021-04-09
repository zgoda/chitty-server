from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generator, List, Mapping, Optional

from redio.pubsub import PubSub

from . import event
from .message import MSG_TYPE_MESSAGE, Message, make_message
from .storage import redis
from .topic import DEFAULT_TOPICS


SYS_USER_DATA = {k: 'server' for k in ['key', 'client_id', 'name']}


@dataclass
class User:
    """User object structure.

    Upon object creation user will be subscribed to private topic, general
    chat and all system topics.

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

    _topics: List[str] = field(init=False, repr=False, default_factory=list)
    _pubsub: Optional[PubSub] = field(init=False, repr=False, default=None)

    def __post_init__(self):
        self._pubsub = redis.pubsub(self.key, *DEFAULT_TOPICS).autodecode.with_channel
        self._pubsub.psubscribe('sys:*')
        self._topics = list(DEFAULT_TOPICS)
        self._topics.append(self.key)

    @classmethod
    def from_map(cls, data: Mapping[str, str]) -> User:
        """Deserialise user data into User object.

        :param data: serialised user data
        :type data: Mapping[str, str]
        :return: User instance
        :rtype: User
        """
        return cls(**data)

    def to_map(self, with_topics: bool = False) -> Mapping[str, str]:
        """Serialise User object into data dictionary.

        :param with_topics: flag whether list of subscribed topics should be
                            returned along with basic data, defaults to False
        :type with_topics: bool, optional
        :return: serialised data
        :rtype: Mapping[str, str]
        """
        data = {
            'key': self.key,
            'clientId': self.client_id,
            'name': self.name,
        }
        if with_topics:
            data['topics'] = list(self._topics)
        return data

    async def subscribe(self, topic: str) -> None:
        """Subscribe to specified topic.

        This effectively creates new topic and this is being broadcast to
        events channel.

        :param topic: topic name
        :type topic: str
        """
        self._pubsub.subscribe(topic)
        self._topics.append(topic)
        await event.new_topic_created(topic)

    async def post_message(self, topic: str, message: str) -> None:
        """Post chat message to a topic.

        This also subscribes user to the topic. If topic does not yet exists,
        it gets created.

        :param topic: topic name
        :type topic: str
        :param message: message text
        :type message: str
        """
        self._pubsub.subscribe(topic)
        kw = {'type': MSG_TYPE_MESSAGE}
        msg_obj = make_message(self.to_map(), topic, message, **kw)
        await msg_obj.publish()
        if topic not in DEFAULT_TOPICS and topic != self.key:
            await event.new_topic_created(topic)

    async def message_stream(self) -> Generator[Message, None, None]:
        """Generator that yields Message objects as they come to pubsub
        receiver.

        :yield: received message and topic wrapped in Message object
        :rtype: Generator[Message, None, None]
        """
        async for topic, message in self._pubsub:
            yield Message(topic=topic, payload=message)


class UserRegistry:
    """Simple user/client registry.

    For now it stores all user/client records locally in dicts.
    """

    def __init__(self):
        self._users_by_client = {}
        self._users_by_key = {}

    def add(self, user: User) -> None:
        """Add user to registry.

        Adding already registered user overwrites previous instance.

        :param user: user object
        :type user: User
        """
        self._users_by_client[user.client_id] = user
        self._users_by_key[user.key] = user

    def get(
                self, *, client_id: Optional[str] = None, key: Optional[str] = None
            ) -> Optional[User]:
        """Retrieve user object from registry.

        Lookup can be done either by client ID or by user identifier (key). At
        least one of these values is required.

        :param client_id: client ID from WebSocker request, defaults to None
        :type client_id: Optional[str], optional
        :param key: user ID (key), defaults to None
        :type key: Optional[str], optional
        :raises RuntimeError: if neither ID or key is provided
        :return: user object or None if not found
        :rtype: Optional[User]
        """
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
        """Remove user from registry.

        Lookup can be done either by client ID or by user identifier (key). At
        least one of these values is required.

        :param client_id: client ID from WebSocker request, defaults to None
        :type client_id: Optional[str], optional
        :param key: user ID (key), defaults to None
        :type key: Optional[str], optional
        :raises RuntimeError: if neither ID or key is provided
        """
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

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Generator, Mapping, Optional

from redio.pubsub import PubSub

from . import event, keys
from .message import MSG_TYPE_MESSAGE, Message, make_message
from .storage import redis
from .topic import DEFAULT_TOPICS


@dataclass
class User:
    """User object structure.

    Upon object creation user will be subscribed to private topic, general
    chat and all system topics.

    :ivar name: user ID
    :type name: str
    :ivar client_id: WS client ID from request
    :type client_id: str
    :ivar key: user key
    :type key: str
    """

    name: str
    created: Optional[datetime] = None

    _topics: set[str] = field(init=False, repr=False, default_factory=set)
    _pubsub: Optional[PubSub] = field(init=False, repr=False, default=None)

    def __post_init__(self):
        self._pubsub = redis.pubsub(self.name, *DEFAULT_TOPICS).autodecode.with_channel
        self._pubsub.psubscribe('sys:*')
        self._topics = set(DEFAULT_TOPICS)
        self._topics.add(self.name)

    @classmethod
    async def find(cls, name: str) -> Optional[User]:
        key = f'{keys.USERS}:{name}'
        data = await redis().hgetall(key)
        if data:
            data.pop('password', None)
            data['created'] = datetime.fromtimestamp(
                float(data['created']), tz=timezone.utc
            )
            user = cls(**data)
            key = f'{keys.TOPICS}:{name}'
            user_topics = await redis().smembers(key)
            for topic in user_topics:
                user.subscribe(topic)
            return user

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
            'name': self.name,
            'created': self.created.timestamp()
        }
        if with_topics:
            data['topics'] = list(self._topics)
        return data

    async def subscribe(self, topic: str) -> None:
        """Subscribe to specified topic.

        If the topic does not exist this creates new topic and broadcast new
        topic created event.

        :param topic: topic name
        :type topic: str
        """
        self._pubsub.subscribe(topic)
        topics = await redis().smembers(keys.TOPICS)
        if topic not in topics:
            await redis().sadd(keys.TOPICS, topic)
            await event.new_topic_created(topic)
        self._topics.add(topic)
        key = f'{keys.TOPICS}:{self.name}'
        await redis().sadd(key, topic)

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
        if topic not in self._topics and topic != self.name:
            self._topics.add(topic)
            key = f'{keys.TOPICS}:{self.name}'
            await redis().sadd(key, topic)
        topics = await redis().smembers(keys.TOPICS)
        if topic != self.name and topic not in topics:
            await redis().sadd(keys.TOPICS, topic)
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
    """Simple user registry.
    """

    def __init__(self):
        self._users = {}

    def add(self, user: User) -> None:
        """Add user to registry.

        Adding already registered user overwrites previous instance.

        :param user: user object
        :type user: User
        """
        self._users[user.name] = user

    def get(self, name: str) -> Optional[User]:
        """Retrieve user object from registry.

        :param name: user ID
        :type name: str
        :return: user object or None if not found
        :rtype: Optional[User]
        """
        return self._users.get(name)

    def remove(self, name: str) -> None:
        """Remove user from registry.

        :param name: user name
        :type name: str
        """
        self._users.pop(name, None)


registry = UserRegistry()

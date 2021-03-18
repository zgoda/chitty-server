import json
import time
from dataclasses import dataclass
from typing import Mapping, Union

from .storage import redis

MSG_TYPE_REGISTER = 'reg'
MSG_TYPE_SUBSCRIBE_TOPIC = 'sub'
MSG_TYPE_DIRECT_MESSAGE = 'dm'
MSG_TYPE_MESSAGE = 'msg'

KNOWN_MSG_TYPES = [
    MSG_TYPE_REGISTER,
    MSG_TYPE_SUBSCRIBE_TOPIC,
    MSG_TYPE_DIRECT_MESSAGE,
    MSG_TYPE_MESSAGE,
]

MSG_FIELDS = {
    MSG_TYPE_REGISTER: ['value'],
    MSG_TYPE_SUBSCRIBE_TOPIC: ['value'],
    MSG_TYPE_DIRECT_MESSAGE: ['to', 'value'],
    MSG_TYPE_MESSAGE: ['to', 'value'],
}


@dataclass
class Message:
    """Message object that can be published.

    :ivar topic: topic where message will be published
    :type topic: str
    :ivar payload: message payload as serialisable structure
    :type payload: Mapping[str, Union[str, float, Mapping[str, str]]]
    """

    topic: str
    payload: Mapping[str, Union[str, float, Mapping[str, str]]]

    async def publish(self):
        """Publish message to Redis PubSub channel (topic).
        """
        await redis().publish(self.topic, json.dumps(self.payload))


def make_message(user_data: dict, topic: str, msg: str, **extra) -> Message:
    """Build chat message structure.

    Any extra data passed in kwargs will be added to message payload.

    :param user_data: serialised user data
    :type user_data: dict
    :param topic: topic name or recipient ID (key)
    :type topic: str
    :param msg: message text
    :type msg: str
    :return: message object
    :rtype: Message
    """
    payload = {
        'from': user_data,
        'message': msg,
        'date': time.time(),
        'topic': topic,
    }
    payload.update(extra)
    return Message(topic=topic, payload=payload)

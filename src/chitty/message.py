import time
from collections import namedtuple

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

Message = namedtuple('Message', ['topic', 'message'])


def make_message(user_data: dict, topic: str, msg: str) -> Message:
    """Build chat message structure.

    :param user_data: serialised user data
    :type user_data: dict
    :param topic: topic name or recipient ID (key)
    :type topic: str
    :param msg: message text
    :type msg: str
    :return: message structure as named tuple
    :rtype: Message
    """
    payload = {
        'from': user_data,
        'message': msg,
        'date': time.time(),
    }
    return Message(topic, payload)

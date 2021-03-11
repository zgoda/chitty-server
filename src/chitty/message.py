import time
from collections import namedtuple

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

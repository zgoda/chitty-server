import json

from .message import make_message
from .storage import redis
from .topic import EVENTS_TOPIC

SYS_USER_DATA = {k: 'server' for k in ['key', 'client_id', 'name']}


async def new_topic_created(topic: str) -> None:
    """Emit event on new topic created.

    :param topic: topic name
    :type topic: str
    """
    topics_num = await redis().sadd('topics', topic)
    if topics_num:
        message = make_message(
            SYS_USER_DATA, EVENTS_TOPIC, f'New topic open: {topic}',
            topic_name=topic,
        )
        await redis().publish(EVENTS_TOPIC, json.dumps(message.message))

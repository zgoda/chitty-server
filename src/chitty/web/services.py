import time
from dataclasses import dataclass, field
from typing import List, Mapping, Optional, Union

import redis

from .. import keys
from ..services.auth import password_context, serializer
from ..topic import DEFAULT_TOPICS
from . import errors


@dataclass
class UserData:
    name: str
    created: float
    topics: List[str] = field(default_factory=list)
    token: Optional[str] = None

    def to_map(self) -> Mapping[str, Union[str, float, List[str]]]:
        return {
            "name": self.name,
            "created": self.created,
            "topics": self.topics,
            "token": self.token or "",
        }


class Storage:
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[int] = None,
    ):
        host = host or "127.0.0.1"
        port = port or 6379
        if database is None:
            database = 0
        self.redis = redis.Redis(
            host=host, port=port, db=database, decode_responses=True
        )

    def user_exists(self, name: str) -> bool:
        key = f"{keys.USERS}:{name}"
        return self.redis.exists(key) != 0

    def add_user(self, name: str, password: str) -> UserData:
        created = time.time()
        pipe = self.redis.pipeline()
        data = {
            "name": name,
            "password": password,
            "created": created,
        }
        pipe.hset(f"{keys.USERS}:{name}", mapping=data)  # type: ignore
        topics = [name]
        topics.extend(DEFAULT_TOPICS)
        pipe.sadd(f"{keys.TOPICS}:{name}", *topics)
        pipe.execute()
        return UserData(name=name, created=created, topics=topics)

    def get_user(self, name) -> UserData:
        created = self.redis.hget(f"{keys.USERS}:{name}", "created")
        topics = self.redis.smembers(f"{keys.TOPICS}:{name}")
        return UserData(name=name, created=created, topics=list(topics))  # type: ignore

    def get_user_topics(self, name) -> List[str]:
        return list(self.redis.smembers(f"{keys.TOPICS}:{name}"))

    def set_auth_token(self, name: str, token: str) -> None:
        key = f"{keys.LOGINS}:{name}"
        self.redis.hset(key, mapping={"token": token, "date": time.time()})

    def get_password(self, name: str) -> Optional[str]:
        key = f"{keys.USERS}:{name}"
        return self.redis.hget(key, "password")


class UserPoolManager:
    def __init__(self, db: Storage):
        self.db = db

    def user_exists(self, name: str) -> bool:
        """Check if user (name) exists in db.

        :param name: user name
        :type name: str
        :return: True if exists, False if not
        :rtype: bool
        """
        return self.db.user_exists(name)

    def create_user(self, name: str, password: str) -> UserData:
        """Create user account.

        Upon succesful account creation an authentication token is returned.

        :param name: user name
        :type name: str
        :param password: user password
        :type password: str
        :raises errors.UserExists: if specified name is already taken
        :return: authentication token
        :rtype: str
        """
        if self.db.user_exists(name):
            raise errors.UserExists("user already exists")
        secret = password_context.hash(password)
        user_data = self.db.add_user(name, secret)
        token = str(serializer.dumps(name))
        self.db.set_auth_token(name, token)
        user_data.token = token
        return user_data

    def login(self, name: str, password: str) -> UserData:
        """Login user.

        Upon succesful login an authentication token is returned.

        :param name: user name
        :type name: str
        :param password: user password
        :type password: str
        :raises errors.UserNotFound: if account does not exist or provided
                                     credentials are invalid
        :return: authentication token
        :rtype: str
        """
        secret = self.db.get_password(name)
        if not secret:
            raise errors.UserNotFound("user does not exist")
        if not password_context.verify(password, secret):
            raise errors.UserNotFound("invalid password")
        user_data = self.db.get_user(name)
        token = str(serializer.dumps(name))
        self.db.set_auth_token(name, token)
        user_data.token = token
        return user_data

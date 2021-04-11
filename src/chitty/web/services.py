import time
from typing import Optional

import redis

from .. import keys
from ..services.auth import password_context, serializer
from . import errors


class Storage:

    def __init__(
                self, host: Optional[str] = None, port: Optional[int] = None,
                database: Optional[int] = None,
            ):
        host = host or '127.0.0.1'
        port = port or 6379
        if database is None:
            database = 0
        self.redis = redis.Redis(
            host=host, port=port, db=database, decode_responses=True
        )

    def user_exists(self, name: str) -> bool:
        key = f'{keys.USERS}:{name}'
        return self.redis.exists(key)

    def add_user(self, name: str, password: str) -> None:
        key = f'{keys.USERS}:{name}'
        self.redis.hset(key, mapping={'name': name, 'password': password})

    def set_auth_token(self, name: str, token: str) -> None:
        key = f'{keys.LOGINS}:{name}'
        self.redis.hset(key, mapping={'token': token, 'date': time.time()})

    def get_password(self, name: str) -> Optional[str]:
        key = f'{keys.USERS}:{name}'
        return self.redis.hget(key, 'password')


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

    def create_user(self, name: str, password: str) -> str:
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
            raise errors.UserExists('user already exists')
        secret = password_context.hash(password)
        self.db.add_user(name, secret)
        token = serializer.dumps(name)
        self.db.set_auth_token(name, token)
        return token

    def login(self, name: str, password: str) -> str:
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
            raise errors.UserNotFound('user does not exist')
        if not password_context.verify(password, secret):
            raise errors.UserNotFound('invalid password')
        token = serializer.dumps(name)
        self.db.set_auth_token(name, token)
        return token

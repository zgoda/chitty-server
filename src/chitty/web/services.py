import hashlib
import os
from typing import Optional

import itsdangerous
import redis
from passlib.context import CryptContext

from . import errors


class Storage:

    KEY_USERS = 'sys:users'
    KEY_LOGINS = 'sys:logins'

    def __init__(
                self, host: Optional[str] = None, port: Optional[int] = None,
                database: Optional[int] = None,
            ):
        if host is None:
            host = '127.0.0.1'
        if port is None:
            port = 6379
        if database is None:
            database = 0
        self.redis = redis.Redis(
            host=host, port=port, db=database, decode_responses=True
        )

    def user_exists(self, name: str) -> bool:
        return self.redis.hexists(self.KEY_USERS, name)

    def add_user(self, name: str, password: str) -> None:
        self.redis.hset(self.KEY_USERS, name, password)

    def set_user_token(self, name: str, token: str) -> None:
        self.redis.hset(self.KEY_LOGINS, name, token)

    def get_password(self, name: str) -> Optional[str]:
        return self.redis.hget(self.KEY_USERS, name)


class UserPoolManager:

    _serializer = itsdangerous.URLSafeTimedSerializer(
        secret_key=os.environ['CHITTY_SECRET_KEY'],
        salt='auth',
        signer_kwargs={'digest_method': hashlib.sha512},
    )
    _pw_ctx = CryptContext(schemes=['argon2'])

    def __init__(self, db: Storage):
        self.db = db

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
        secret = self._pw_ctx.hash(password)
        self.db.add_user(name, secret)
        token = self._serializer.dumps(name)
        self.db.set_user_token(name, token)
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
        if not self._pw_ctx.verify(password, secret):
            raise errors.UserNotFound('invalid password')
        token = self._serializer.dumps(name)
        self.db.set_user_token(name, token)
        return token

import os

import itsdangerous
from passlib.context import CryptContext

from .storage import KEY_USER_CREDENTIALS, redis

pw_context = CryptContext(schemes=['argon2'])
serializer = itsdangerous.URLSafeTimedSerializer(os.environ['CHITTY_SECRET_KEY'])


async def user_exists(name: str) -> bool:
    """Check if user exists in pool.

    :param name: user name
    :type name: str
    :return: True if user exists
    :rtype: bool
    """
    return bool(await redis().hexists(KEY_USER_CREDENTIALS, name))


async def check_password(name: str, password: str) -> bool:
    """Check if password matches stored secret.

    :param name: user name
    :type name: str
    :param password: user supplied password
    :type password: str
    :return: verification result
    :rtype: bool
    """
    stored_secret = await redis().hget(KEY_USER_CREDENTIALS, name)
    return pw_context.verify(password, stored_secret)


async def create_credentials(name: str, password: str):
    """Store user credentials.

    :param name: user name
    :type name: str
    :param password: user supplied password
    :type password: str
    """
    stored_secret = pw_context.hash(password)
    await redis().hset(KEY_USER_CREDENTIALS, {name: stored_secret})


def generate_token(value: str) -> str:
    """Generate access token with time signature.

    :param value: value to be encoded as payload
    :type value: str
    :return: token string
    :rtype: str
    """
    return serializer.dumps(value)


def decode_token(token: str) -> str:
    """Decode payload from access token.

    If any signature related error is encountered (expired, tampered, etc),
    this function returns empty string.

    :param token: token string
    :type token: str
    :return: payload value or empty string
    :rtype: str
    """
    try:
        return serializer.loads(token, max_age=24*60*60)
    except (itsdangerous.SignatureExpired, itsdangerous.BadSignature):
        return ''

import hashlib
import os
from collections import namedtuple
from enum import Enum

import itsdangerous
from itsdangerous.exc import BadSignature, SignatureExpired
from passlib.context import CryptContext

serializer = itsdangerous.URLSafeTimedSerializer(
    secret_key=os.environ['CHITTY_SECRET_KEY'],
    salt='auth',
    signer_kwargs={'digest_method': hashlib.sha512},
)
password_context = CryptContext(schemes=['argon2'])


class ResultType(Enum):
    OK = None
    EXPIRED = 'expired'
    BADSIG = 'bad signature'


TokenCheckResult = namedtuple('TokenCheckResult', ['result', 'value'], defaults=[None])


def get_token(data: str) -> str:
    """Generate authentication token containing specified data.

    :param data: data to be serialised in token
    :type data: str
    :return: token string
    :rtype: str
    """
    return serializer.dumps(data)


def check_token(token: str) -> TokenCheckResult:
    """Deserialise token content.

    This validates token signature. Returned namedtuple object contains both
    check result and token payload. If the signature is invalid, then payload
    is None.

    :param token: token string
    :type token: str
    :return: deserialisation result
    :rtype: TokenCheckResult
    """
    value = None
    max_age = int(os.getenv('CHITTY_TOKEN_MAX_AGE', str(24*60*60)))
    try:
        rt = ResultType.OK
        value = serializer.loads(token, max_age=max_age)
    except SignatureExpired:
        rt = ResultType.EXPIRED
    except BadSignature:
        rt = ResultType.BADSIG
    return TokenCheckResult(result=rt, value=value)

import os

import itsdangerous
from passlib.context import CryptContext
from quart import request
from quart_trio import QuartTrio
from trio_parallel import run_sync

from .errors import E_WEB_BADREQ, E_WEB_NOTFOUND
from .storage import KEY_USER_CREDENTIALS, redis
from .utils import error_response

pw_context = CryptContext(schemes=['argon2'])

app = QuartTrio(__name__.split('.')[0])


def _check_password(password: str, secret: str) -> bool:
    return pw_context.verify(password, secret)


def _gen_password(password: str) -> str:
    return pw_context.hash(password)


async def check_password(name: str, password: str) -> bool:
    stored_secret = await redis().hget(KEY_USER_CREDENTIALS, name)
    return await run_sync(_check_password, password, stored_secret)


async def create_credentials(name: str, password: str):
    stored_secret = await run_sync(_gen_password, password)
    await redis().hset(KEY_USER_CREDENTIALS, {name: stored_secret})


def generate_token(value: str) -> str:
    serializer = itsdangerous.URLSafeSerializer(os.environ['CHITTY_SECRET_KEY'])
    return serializer.dumps(value)


def decode_token(token: str) -> str:
    serializer = itsdangerous.URLSafeSerializer(os.environ['CHITTY_SECRET_KEY'])
    return serializer.loads(token)


@app.route('/login', methods=['POST'])
async def login():
    data = await request.form
    name = data['name']
    password = data['password']
    auth_result = await check_password(name, password)
    if auth_result:
        return {'token': generate_token(name)}
    return error_response(E_WEB_NOTFOUND, message='invalid credentials')


@app.route('/register', methods=['POST'])
async def register():
    data = await request.form
    name = data['name']
    password = data['password']
    user_exists = bool(await redis().hexists(KEY_USER_CREDENTIALS, name))
    if user_exists:
        return error_response(E_WEB_BADREQ, 'user already exists')
    await create_credentials(name, password)
    return {'token': generate_token(name)}

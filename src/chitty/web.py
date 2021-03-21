import os

import itsdangerous
from passlib.context import CryptContext
from quart import request
from quart_trio import QuartTrio

from .errors import E_WEB_BADREQ, E_WEB_NOTFOUND
from .storage import KEY_USER_CREDENTIALS, redis
from .utils import error_response

pw_context = CryptContext(schemes=['argon2'])

app = QuartTrio(__name__.split('.')[0])


async def check_password(name: str, password: str) -> bool:
    stored_secret = await redis().hget(KEY_USER_CREDENTIALS, name)
    return pw_context.verify(password, stored_secret)


async def create_credentials(name: str, password: str):
    stored_secret = pw_context.hash(password)
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

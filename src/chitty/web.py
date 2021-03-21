import os
import multiprocessing

import itsdangerous
import nanoid
import trio
from passlib.context import CryptContext
from quart import request
from quart_trio import QuartTrio
from trio_parallel import run_sync

from .errors import E_WEB_NOTFOUND
from .storage import redis
from .utils import error_response

pw_context = CryptContext(schemes=['argon2'])

app = QuartTrio(__name__.split('.')[0])


async def check_password(nursery: trio.Nursery, name: str, password: str) -> bool:
    stored_secret = await redis().hget('sys:usercreds', name)
    async with nursery:
        return await run_sync(pw_context.verify, password, stored_secret)


def generate_token(value: str) -> str:
    serializer = itsdangerous.URLSafeSerializer(os.environ['CHITTY_SECRET_KEY'])
    return serializer.dumps(value)


def decode_token(token: str) -> str:
    serializer = itsdangerous.URLSafeSerializer(os.environ['CHITTY_SECRET_KEY'])
    return serializer.loads(token)


@app.route('/login', methods=['POST'])
async def login():
    name = request.form['name']
    password = request.form['password']
    multiprocessing.freeze_support()
    auth_result = await check_password(app.nursery, name, password)
    if auth_result:
        return {'token': nanoid.generate()}
    return error_response(E_WEB_NOTFOUND, message='invalid credentials')


@app.route('/register', methods=['POST'])
async def register():
    pass

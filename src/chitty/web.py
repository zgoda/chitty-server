from quart import request
from quart_trio import QuartTrio

from .auth import check_password, create_credentials, generate_token, user_exists
from .errors import E_WEB_BADREQ, E_WEB_NOTFOUND
from .utils import error_response

app = QuartTrio(__name__.split('.')[0])


@app.route('/login', methods=['POST'])
async def login():
    data = await request.form
    name = data['name']
    password = data['password']
    auth_result = await check_password(name, password)
    if auth_result:
        return {'token': generate_token(name)}
    return error_response(E_WEB_NOTFOUND, message='invalid credentials'), 404


@app.route('/register', methods=['POST'])
async def register():
    data = await request.form
    name = data['name']
    password = data['password']
    user_valid = await user_exists(name)
    if user_valid:
        return error_response(E_WEB_BADREQ, 'user already exists'), 400
    await create_credentials(name, password)
    return {'token': generate_token(name)}

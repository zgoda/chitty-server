import os

import falcon

from .auth import UserLoginResource, UserRegistrationResource
from .middleware import cors
from .services import Storage, UserPoolManager

_resources = {}


class App(falcon.API):

    def __init__(self, *args, **kw):
        env = os.getenv('CHITTY_ENV', 'production')
        if env == 'development':
            middlewares = kw.setdefault('middleware', [])
            try:
                iter(middlewares)
            except TypeError:
                middlewares = [middlewares]
            middlewares.append(cors)
        super().__init__(*args, **kw)
        self.storage = Storage()
        self.user_mgr = UserPoolManager(self.storage)
        self.register_routes()

    def init_resources(self):
        register = _resources.get('register')
        if register is None:
            _resources['register'] = UserRegistrationResource(self.user_mgr)
        login = _resources.get('login')
        if login is None:
            _resources['login'] = UserLoginResource(self.user_mgr)

    def register_routes(self):
        self.init_resources()
        self.add_route('/register', _resources['register'])
        self.add_route('/login', _resources['login'])


def make_app() -> App:
    return App()

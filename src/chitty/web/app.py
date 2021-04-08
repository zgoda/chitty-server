import os

import falcon

from .auth import UserLoginResource, UserRegistrationResource
from .services import Storage, UserPoolManager

_resources = {}


class App(falcon.App):

    def __init__(self, *args, **kw):
        env = os.getenv('CHITTY_ENV', 'production')
        if env == 'development':
            kw.setdefault('cors_enable', True)
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

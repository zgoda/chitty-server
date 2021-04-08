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
        self.user_mgr = UserPoolManager(Storage())
        self.register_routes()

    def register_routes(self):
        _resources.setdefault('register', UserRegistrationResource(self.user_mgr))
        _resources.setdefault('login', UserLoginResource(self.user_mgr))
        self.add_route('/register', _resources['register'])
        self.add_route('/login', _resources['login'])


def make_app() -> App:
    return App()

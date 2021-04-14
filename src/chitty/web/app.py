import os

import falcon

from .auth import UserLoginResource, UserNamesResource, UserRegistrationResource
from .meta import ServerMetadataResource
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
        reg = _resources.setdefault('register', UserRegistrationResource(self.user_mgr))
        login = _resources.setdefault('login', UserLoginResource(self.user_mgr))
        names = _resources.setdefault('names', UserNamesResource(self.user_mgr))
        meta = _resources.setdefault('meta', ServerMetadataResource())
        self.add_route('/register', reg)
        self.add_route('/login', login)
        self.add_route('/names/{name}', names)
        self.add_route('/meta', meta)


def make_app() -> App:
    return App()

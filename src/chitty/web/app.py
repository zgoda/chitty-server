import falcon

from .services import Storage, UserPoolManager
from .auth import UserRegistrationResource, UserLoginResource

_resources = {}


class App(falcon.API):

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.storage = Storage()
        self.user_mgr = UserPoolManager(self.storage)
        self.init_resources()
        self.register_routes()

    def init_resources(self):
        register = _resources.get('register')
        if register is None:
            _resources['register'] = UserRegistrationResource(self.user_mgr)
        login = _resources.get('login')
        if login is None:
            _resources['login'] = UserLoginResource(self.user_mgr)

    def register_routes(self):
        self.add_route('/register', _resources['register'])
        self.add_route('/login', _resources['login'])


def make_app() -> App:
    return App()

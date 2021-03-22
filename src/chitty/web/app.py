import falcon

from .services import Storage, UserPoolManager


class App(falcon.API):

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.storage = Storage()
        self.user_mgr = UserPoolManager(self.storage)
        self.register_routes()

    def register_routes(self):
        pass


application = App()

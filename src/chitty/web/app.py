import falcon


class App(falcon.API):

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.register_routes()

    def register_routes(self):
        pass


application = App()

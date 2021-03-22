import falcon
from falcon import Request, Response

from .errors import UserExists
from .services import UserPoolManager


class UserRegistrationResource:

    def __init__(self, user_manager: UserPoolManager):
        self.user_mgr = user_manager

    def on_post(self, req: Request, resp: Response) -> None:
        data = req.media
        resp.status = falcon.HTTP_200
        try:
            token = self.user_mgr.create_user(data['name'], data['password'])
            resp.media = {'token': token}
            return
        except UserExists:
            resp.media = {'error': 'user already exists'}
            resp.status = falcon.HTTP_400

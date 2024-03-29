import falcon
from falcon import Request, Response

from ..utils import error_response
from .errors import UserExists, UserError
from .services import UserPoolManager


class UserNamesResource:
    def __init__(self, user_manager: UserPoolManager):
        self.user_mgr = user_manager

    def on_get(self, req: Request, resp: Response, name: str) -> None:
        resp.headers["Content-Type"] = "text/plain"
        if self.user_mgr.user_exists(name):
            resp.status = falcon.HTTP_400


class UserRegistrationResource:
    def __init__(self, user_manager: UserPoolManager):
        self.user_mgr = user_manager

    def on_post(self, req: Request, resp: Response) -> None:
        data = req.media
        resp.status = falcon.HTTP_200
        try:
            user_data = self.user_mgr.create_user(data["name"], data["password"])
            resp.media = user_data.to_map()
        except UserExists:
            code = falcon.HTTP_400[:3]
            resp.media = error_response(reason=code, message="user already exists")
            resp.status = falcon.HTTP_400


class UserLoginResource:
    def __init__(self, user_manager: UserPoolManager):
        self.user_mgr = user_manager

    def on_post(self, req: Request, resp: Response) -> None:
        data = req.media
        resp.status = falcon.HTTP_200
        try:
            user_data = self.user_mgr.login(data["name"], data["password"])
            resp.media = user_data.to_map()
        except UserError:
            code = falcon.HTTP_404[:3]
            resp.media = error_response(
                reason=code, message="no user with provided credentials"
            )
            resp.status = falcon.HTTP_404

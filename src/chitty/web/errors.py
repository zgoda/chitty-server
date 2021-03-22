class ChittyError(Exception):
    pass


class UserError(ChittyError):
    pass


class UserExists(UserError):
    pass


class UserNotFound(UserError):
    pass

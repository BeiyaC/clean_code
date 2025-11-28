class EmailAlreadyExistError(Exception):
    pass


class UnauthorizedError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class CardNotFoundError(Exception):
    pass


class AuthorizationError(Exception):
    pass


class AcknowledgeUploadError(Exception):
    pass


class BadUserInputError(Exception):
    pass

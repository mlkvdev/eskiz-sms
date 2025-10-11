class EskizException(Exception):
    def __init__(self, message=None, status=None, status_code: int = None):
        self.status = status
        self.message = message
        message = str(message) if message else ''
        if status:
            message += f"; status={status}"
        if status_code:
            message += f"; status_code={status_code}"
        super(EskizException, self).__init__(message.strip())


class BadRequest(EskizException):
    pass


class InvalidCredentials(EskizException):
    pass


class InvalidCallbackUrl(EskizException):
    pass


class TokenBlackListed(EskizException):
    pass


class TokenInvalid(EskizException):
    pass


class TokenExpiredException(EskizException):
    pass


class ContactNotFound(EskizException):
    pass


class HTTPError(EskizException):
    pass

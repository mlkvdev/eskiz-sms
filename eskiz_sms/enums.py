from enum import Enum


class Status(str, Enum):
    TOKEN_INVALID = "token-invalid"


class Message(str, Enum):
    EXPIRED_TOKEN = "Expired"
    INVALID_CREDENTIALS = "Неверный Email или пароль"

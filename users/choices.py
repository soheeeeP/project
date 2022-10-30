from enum import Enum


class ChoicesEnum(Enum):
    @classmethod
    def choices(cls):
        return tuple((i.name, i.value) for i in cls)


class AuthOtpTypeEnum(ChoicesEnum):
    EMAIL = 'email'
    PASSWORD_RESET = 'password_reset'


class LoginTypeEnum(ChoicesEnum):
    EMAIL = 'email'
    PHONE_NUMBER = 'phone_number'
    USERNAME = 'username'
    NICKNAME = 'nickname'

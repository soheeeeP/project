from enum import Enum


class ChoicesEnum(Enum):
    @classmethod
    def choices(cls):
        return tuple((item.value, item.value) for i, item in enumerate(cls))

    @classmethod
    def choices_list(cls):
        return list(item.value for i, item in enumerate(cls))


class AuthOtpTypeEnum(ChoicesEnum):
    EMAIL = 'email'
    PASSWORD_RESET = 'password_reset'


class LoginTypeEnum(ChoicesEnum):
    EMAIL = 'email'
    PHONE_NUMBER = 'phone_number'
    USERNAME = 'username'
    NICKNAME = 'nickname'

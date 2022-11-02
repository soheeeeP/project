import random
import pyotp
import factory
from factory import fuzzy
from users.models import User, AuthOtp
from users.choices import AuthOtpTypeEnum

otp_register_code = fuzzy.FuzzyInteger(low=100000, high=999999)


def _rand_str():
    return str(random.randint(1000, 9999))


def generate_phone_number_string():
    return "-".join(["010", _rand_str(), _rand_str()])


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ["username", "nickname", "phone_number", "password"]

    email = factory.LazyAttribute(lambda o: '%s@example.com' % o.username)
    username = fuzzy.FuzzyText(length=15)
    nickname = fuzzy.FuzzyText(length=15)
    password = fuzzy.FuzzyText(length=10)
    phone_number = factory.LazyAttribute(lambda o: generate_phone_number_string())


class AuthOtpFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AuthOtp
        django_get_or_create = ["number"]

    auth_type = fuzzy.FuzzyChoice(choices=AuthOtpTypeEnum.choices_list())
    number = factory.LazyAttribute(lambda o: "-".join(["010", _rand_str(), _rand_str()]))
    otp_key = factory.LazyAttribute(lambda o: pyotp.random_base32())
    authenticated = factory.LazyAttribute(lambda o: random.getrandbits(0))

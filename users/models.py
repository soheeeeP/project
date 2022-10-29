import datetime
import pyotp
from typing import Any
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager as BaseManager
from django.core.exceptions import ValidationError
from project.conf import app_settings


class UserManager(BaseManager):
    def validate_request_kwargs(self, **kwargs) -> None:
        required_fields = [
            "email",
            "username",
            "nickname",
            "password",
            "phone_number",
            "otp_register_code"
        ]
        for field_name in required_fields:
            if not kwargs.get(field_name, None):
                raise ValidationError(f"{field_name}_field_required")

    def create_authenticated_user_from_request(self, **kwargs: Any):
        self.validate_request_kwargs(**kwargs)
        kwargs["email"] = self.normalize_email(kwargs["email"])
        user: User = self.model(**kwargs)
        user.set_password(kwargs["password"])
        user.save(using=self._db)

    def create_superuser_from_server(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        user: User = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save()


class User(AbstractUser):
    email = models.EmailField(
        unique=True,
        max_length=255,
        verbose_name='이메일'
    )
    username = models.CharField(
        max_length=150,
        verbose_name='이름'
    )
    nickname = models.CharField(
        max_length=150,
        verbose_name='닉네임'
    )
    phone_number = models.CharField(
        max_length=17,
        verbose_name='휴대폰 번호',
        null=False,
        blank=False
    )
    otp_register_code = models.CharField(max_length=6)
    authenticated = models.BooleanField(
        default=False,
        verbose_name='휴대폰 인증 여부'
    )

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "nickname", "phone_number"]

    class Meta:
        db_table = "User"
        verbose_name = "사용자"


class AuthOtp(models.Model):
    number = models.CharField(
        max_length=17,
        verbose_name='휴대폰 번호',
        null=False,
        blank=False
    )
    otp_key = models.CharField(max_length=128)
    otp_register_code = models.CharField(max_length=6, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "AuthOtp"
        verbose_name = "인증"
        ordering = ['-timestamp']
        get_latest_by = ['timestamp']

    def authenticate_code_by_otp_key(self, code):
        t = pyotp.TOTP(self.otp_key, interval=app_settings.OTP_TIME_INTERVAL)
        valid = t.verify(str(code))
        if valid:
            self.otp_register_code = code
        return valid

    @property
    def otp_code(self) -> str:
        t = pyotp.TOTP(self.otp_key, interval=app_settings.OTP_TIME_INTERVAL)
        return str(t.at(datetime.datetime.now()))

    @property
    def otp_interval(self) -> int:
        return pyotp.TOTP(self.otp_key, interval=app_settings.OTP_TIME_INTERVAL).interval

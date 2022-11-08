import re
import datetime

from django.contrib.auth.hashers import check_password
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from project.conf import app_settings
from users.fields import ChoiceTypeField
from users.models import AuthOtp, User
from users.choices import AuthOtpTypeEnum, LoginTypeEnum


class AuthOtpSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthOtp
        fields = "__all__"


class AuthOtpSendSMSSerializer(serializers.ModelSerializer):
    auth_type = ChoiceTypeField(
        choices=AuthOtpTypeEnum.choices(),
        default=AuthOtpTypeEnum.EMAIL.value,
        required=False,
        valid_choice={"auth_type": AuthOtpTypeEnum.choices_list()}
    )

    class Meta:
        model = AuthOtp
        fields = ["number", "auth_type"]

    def validate_number(self, value):
        regex = re.match(r'^(010|070)-\d{3,4}-\d{4}$', value)
        if not regex:
            raise ValidationError(detail={"detail": "invalid_number", "number_format": ["010-0000-0000"]})
        return regex.string

    def save(self, **kwargs):
        try:
            auth_otp = self.Meta.model.objects.filter(**self.validated_data, authenticated=False).latest()
        except self.Meta.model.DoesNotExist:
            auth_otp = self.Meta.model.objects.create(**self.validated_data)

        self.instance = auth_otp
        return auth_otp

    def to_representation(self, instance: AuthOtp):
        expired_dt = self.instance.timestamp + datetime.timedelta(0, self.instance.otp_interval)
        data = super().to_representation(self.instance)
        data.pop('auth_type')
        data.update({
            'otp_code': self.instance.otp_code,
            'expired_at': expired_dt.strftime('%Y-%m-%d %H:%M:%S')
        })
        return data


class AuthOtpVerifyCodeSerializer(serializers.ModelSerializer):
    otp_code = serializers.CharField(max_length=128)
    otp_register_code = serializers.CharField(max_length=128, required=False)
    verified_at = serializers.DateTimeField(required=False)
    auth_type = ChoiceTypeField(
        choices=AuthOtpTypeEnum.choices(),
        default=AuthOtpTypeEnum.EMAIL.value,
        required=False,
        valid_choice={"auth_type": AuthOtpTypeEnum.choices_list()}
    )

    class Meta:
        model = AuthOtp
        fields = ["number", "otp_code", "verified_at", "auth_type", "otp_register_code"]

    def validate_number(self, value):
        try:
            instance = self.Meta.model.objects.filter(number=value).latest()
            self.instance = instance
        except self.Meta.model.DoesNotExist:
            raise ValidationError("invalid_number")
        return value

    def validate_auth_type(self, value):
        default_auth_type = self.get_fields().get('auth_type').default
        auth_type = value or default_auth_type
        try:
            assert self.instance.auth_type == auth_type
        except AssertionError:
            raise ValidationError(detail={"detail": "invalid_auth_type", "auth_type": dict(AuthOtpTypeEnum.choices())})
        return auth_type

    def save(self, **kwargs):
        otp_code = self.validated_data.pop("otp_code")
        verified = self.instance.authenticate_code_by_otp_key(otp_code)
        if not verified:
            raise ValidationError("invalid_code")
        self.validated_data.update({"otp_register_code": otp_code})
        if self.instance is not None:
            self.instance = self.update(self.instance, self.validated_data)
            self.verified_at = datetime.datetime.now()
        else:
            raise ValidationError("invalid_number")
        return self.instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop('otp_code')
        data.pop('otp_register_code')
        data.pop('auth_type')
        data.update({'verified_at': self.verified_at.strftime('%Y-%m-%d %H:%M:%S')})
        return data


class SignupSerializer(serializers.ModelSerializer):
    auth_otp = AuthOtpSerializer(required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "nickname",
            "password",
            "phone_number",
            "otp_register_code",
            "auth_otp"
        ]

    def validate(self, attrs):
        number = attrs["phone_number"]
        try:
            auth_otp = AuthOtp.objects.filter(number=number, authenticated=False).latest()
            assert str(auth_otp.otp_register_code) == str(attrs["otp_register_code"])
            self.auth_otp = auth_otp
        except AuthOtp.DoesNotExist:
            raise ValidationError("invalid_number")
        except AssertionError:
            raise ValidationError("unauthenticated_otp")
        return attrs

    def save(self, **kwargs):
        with transaction.atomic():
            user = self.Meta.model.objects.create_authenticated_user_from_request(**self.validated_data)
            self.auth_otp.authenticated = True
            self.auth_otp.save()
            return user

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop("otp_register_code")
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "nickname",
            "phone_number",
            "is_staff",
            "last_login_type",
            "last_login_datetime"
        ]


class LoginSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField(max_length=255)
    phone_number = serializers.CharField(max_length=17)
    username = serializers.CharField(max_length=150)
    nickname = serializers.CharField(max_length=150)
    password = serializers.CharField(required=True)
    login_type = ChoiceTypeField(
        choices=LoginTypeEnum.choices(),
        default=LoginTypeEnum.EMAIL.value,
        required=False,
        valid_choice={"login_type": LoginTypeEnum.choices_list()}
    )

    def validate(self, attrs):
        default_login_type = self.get_fields().get('login_type').default
        login_type = attrs.get("login_type", default_login_type)
        filter_kwargs = {login_type: attrs[login_type]}
        try:
            user = User.objects.get(Q(**filter_kwargs))
            if not user.check_password(attrs["password"]):
                raise ValidationError("wrong_password")
        except User.DoesNotExist:
            raise ValidationError("no_exist_user")

        refresh = self.get_token(user)
        data = {
            "user": UserSerializer(user).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }
        if app_settings.SIMPLE_JWT_UPDATE_LOGIN_SETTING:
            user.last_login_datetime = timezone.now()
            user.last_login_type = default_login_type
            user.save(update_fields=["last_login_datetime", "last_login_type"])

        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop("login_type")
        return data


class PasswordSerializer(serializers.Serializer):
    number = serializers.CharField(required=True)
    otp_code = serializers.CharField(max_length=6, required=True)
    new_passwd = serializers.CharField(required=True)
    user = UserSerializer(required=False)

    def validate_number(self, value):
        regex = re.match(r'^(010|070)-\d{3,4}-\d{4}$', value)
        if not regex:
            raise ValidationError(detail={"detail": "invalid_number", "number_format": "010-0000-0000"})
        return regex.string

    def validate(self, attrs):
        number = attrs["number"]
        try:
            auth_otp = AuthOtp.objects.filter(
                number=number,
                authenticated=False,
                auth_type=AuthOtpTypeEnum.PASSWORD_RESET.value
            ).latest()
        except AuthOtp.DoesNotExist:
            raise ValidationError("invalid_number_or_code")
        try:
            assert auth_otp.auth_type == AuthOtpTypeEnum.PASSWORD_RESET.value
            assert str(auth_otp.otp_register_code) == str(attrs["otp_code"])
        except AssertionError:
            raise ValidationError("invalid_auth_otp_data")

        try:
            user = User.objects.get(phone_number=number)
            self.user = user
        except User.DoesNotExist:
            raise ValidationError("no_exist_user")

        if check_password(attrs["new_passwd"], self.user.password):
            raise ValidationError("previous_passwd")

        auth_otp.authenticated = True
        auth_otp.save()

        return attrs

    def save(self, **kwargs):
        self.user.set_password(self.validated_data["new_passwd"])
        self.user.save()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop("otp_code")
        return data

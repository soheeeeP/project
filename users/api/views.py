import json

from rest_framework import viewsets, status, permissions, throttling
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt import authentication
from users.models import AuthOtp, User
from users.choices import AuthOtpTypeEnum
from .exceptions import Throttled, NotAuthenticated, PermissionDenied
from .serializers import (
    AuthOtpSendSMSSerializer,
    AuthOtpVerifyCodeSerializer,
    LoginSerializer,
    SignupSerializer,
    UserSerializer,
    PasswordSerializer
)
from project.conf import app_settings


class BaseViewSet(viewsets.ModelViewSet):
    lookup_data_key = None

    def throttled(self, request, wait):
        raise Throttled(wait)

    def permission_denied(self, request, message=None, code=None):
        if request.authenticators and not request.successful_authenticator:
            raise NotAuthenticated()
        raise PermissionDenied

    def get_object_by_data(self):
        queryset = self.get_queryset()
        if self.lookup_data_key not in self.request.data:
            return queryset.none()
        filter_kwargs = {self.lookup_data_key: self.request.data[self.lookup_data_key]}
        filtered_queryset = queryset.filter(**filter_kwargs)
        return filtered_queryset.latest() if filtered_queryset else filtered_queryset

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = kwargs.pop('instance', self.get_object_by_data())
        serializer = self.get_serializer(
            instance=instance,
            data=self.request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class AuthViewSet(BaseViewSet):
    lookup_data_key = 'number'
    queryset = AuthOtp.objects.all()
    serializer_class = AuthOtpSendSMSSerializer
    throttle_scope = app_settings.REST_FRAMEWORK_DEFAULT_THROTTLE_RATES.get('default')

    def set_throttles(self):
        if self.request.user.is_anonymous:
            self.throttle_scope = 'user.' + self.action
            throttle_classes = [throttling.ScopedRateThrottle]
        else:
            throttle_classes = app_settings.REST_FRAMEWORK_THROTTLE_CLASSES
        self.throttle_classes = [throttle() for throttle in throttle_classes]

    def get_throttles(self):
        self.set_throttles()
        return self.throttle_classes

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[permissions.AllowAny]
    )
    def send_code(self, request) -> Response:
        return self.create(request)

    @action(
        detail=False,
        methods=["post", "put"],
        permission_classes=[permissions.AllowAny],
        serializer_class=AuthOtpVerifyCodeSerializer
    )
    def verify_code(self, request) -> Response:
        return self.update(request, partial=True)


class UserViewSet(BaseViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def set_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        self.permission_classes = [perm() for perm in permission_classes]

    def get_permissions(self):
        self.set_permissions()
        return self.permission_classes

    @action(
        detail=False,
        methods=["post"],
        serializer_class=SignupSerializer
    )
    def signup(self, request):
        return self.create(request)

    @action(
        detail=False,
        methods=["post"],
        serializer_class=LoginSerializer,
        url_path=r"login"
    )
    def user_login(self, request):
        serializer = self.get_serializer(data=self.request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=["get", "put"],
        authentication_classes=[authentication.JWTAuthentication],
        url_path=r"detail"
    )
    def user_detail(self, request):
        if request.method == "GET":
            user = self.request.user
            return Response({"user": UserSerializer(user).data}, status=status.HTTP_200_OK)
        return self.update(request, instance=self.request.user, partial=True)


class PassWordViewSet(BaseViewSet):
    lookup_data_key = 'number'
    queryset = AuthOtp.objects.all()
    serializer_class = PasswordSerializer
    throttle_scope = app_settings.REST_FRAMEWORK_DEFAULT_THROTTLE_RATES.get('default')

    @action(
        detail=False,
        methods=["post"],
        serializer_class=AuthOtpSendSMSSerializer,
        url_path=r"request_code"
    )
    def passwd_request_code(self, request):
        self.request.data.update({"auth_type": AuthOtpTypeEnum.PASSWORD_RESET.value})
        return self.create(request)

    @action(
        detail=False,
        methods=["post", "put"],
        serializer_class=AuthOtpVerifyCodeSerializer,
        url_path=r"verify_code"
    )
    def passwd_verify_code(self, request):
        self.request.data.update({"auth_type": AuthOtpTypeEnum.PASSWORD_RESET.value})
        return self.update(request, partial=True)

    @action(detail=False, methods=["post", "put"], url_path=r"reset")
    def passwd_reset(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

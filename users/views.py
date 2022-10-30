from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt import authentication
from .models import AuthOtp, User
from .serializers import (
    AuthOtpSendSMSSerializer,
    AuthOtpVerifyCodeSerializer,
    LoginSerializer,
    SignupSerializer,
    UserSerializer,
    PasswordSerializer
)


class BaseViewSet(viewsets.ModelViewSet):
    lookup_data_key = None

    def get_object_by_data(self):
        queryset = self.get_queryset()
        if self.lookup_data_key not in self.request.data:
            return queryset.none()
        filter_kwargs = {self.lookup_data_key: self.request.data[self.lookup_data_key]}
        filtered_queryset = queryset.filter(**filter_kwargs)
        return filtered_queryset.latest() if filtered_queryset else filtered_queryset

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object_by_data()
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
        if request.method == "PUT":
            return self.update(request, partial=True)
        return self.update(request)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [perm() for perm in permission_classes]

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
        url_path=r"user/login"
    )
    def user_login(self, request):
        serializer = self.get_serializer(data=self.request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=["get", "put"],
        authentication_classes=authentication.JWTAuthentication,
        url_path=r"user/"
    )
    def user_detail(self, request):
        if request.method == "GET":
            user = self.get_object()
            return Response(user, status=status.HTTP_200_OK)
        return self.update(request)


class PassWordViewSet(BaseViewSet):
    lookup_data_key = 'number'
    serializer_class = PasswordSerializer

    @action(
        detail=False,
        methods=["post"],
        serializer_class=AuthOtpSendSMSSerializer,
        url_path=r"passwd/request"
    )
    def passwd_request_code(self, request):
        self.request.data.update({"auth_type": "password_reset"})
        return self.create(request)

    @action(
        detail=False,
        methods=["post", "put"],
        serializer_class=AuthOtpVerifyCodeSerializer,
        url_path=r"passwd/confirm"
    )
    def passwd_confirm_code(self, request):
        self.request.data.update({"auth_type": "password_reset"})
        if request.method == "PUT":
            return self.update(request, partial=True)
        return self.update(request)

    @action(detail=False, url_path=r"passwd/reset")
    def passwd_reset(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()


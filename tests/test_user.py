from django.contrib.auth.hashers import make_password
from factory import fuzzy
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from users.choices import AuthOtpTypeEnum
from .factories import UserFactory, AuthOtpFactory, generate_phone_number_string
from users.models import User, AuthOtp


class UserTestCase(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.url_prefix = "http://127.0.0.1:8000/"

    def test_user_signup(self):
        url = self.url_prefix + "user/signup/"

        # 실패: 인증되지 않은 번호를 사용하여 회원가입을 하려는 경우
        auth: AuthOtp = AuthOtpFactory.create()
        data = {
            "phone_number": auth.number,
            "otp_register_code": auth.otp_code,
            "email": "email@gmail.com",
            "username": "username",
            "nickname": "nickname",
            "password": "password"
        }
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "unauthenticated_otp" in response.data

        # 실패: 인증 정보가 없는 번호를 사용하여 회원가입을 하려는 경우
        data2 = {
            "phone_number": generate_phone_number_string(),
            "otp_register_code": auth.otp_code,
            "email": "email@gmail.com",
            "username": "username",
            "nickname": "nickname",
            "password": "password"
        }
        response = self.client.post(url, data2)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid_number" in response.data

        # 성공
        self.client.post(
            self.url_prefix + "auth/verify_code/",
            {"number": auth.number, "otp_code": auth.otp_code}
        )
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data.get("email") == data.get("email")
        assert response.data.get("username") == data.get("username")
        assert response.data.get("nickname") == data.get("nickname")
        assert response.data.get("password") == data.get("password")

        # 실패: 이미 타인의 계정 등록시 사용된 인증정보(번호)를 사용하여 회원가입 하려는 경우
        data3 = {
            "phone_number": auth.number,
            "otp_register_code": auth.otp_code,
            "email": "email3@gmail.com",
            "username": "username",
            "nickname": "nickname",
            "password": "password"
        }
        response = self.client.post(url, data3)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid_number" in response.data

    def test_user_login(self):
        url = self.url_prefix + "user/login/"

        # 성공: 이메일 로그인
        auth: AuthOtp = AuthOtpFactory.create()
        self.client.post(
            self.url_prefix + "auth/verify_code/",
            {"number": auth.number, "otp_code": auth.otp_code}
        )
        user: User = UserFactory.create(
            phone_number=auth.number,
            otp_register_code=auth.otp_code,
            password=make_password("password")
        )
        response = self.client.post(url, {"email": user.email, "password": "password"})
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data.get("user").get("email") == user.email
        del response

        # 실패: 잘못된 이메일로 로그인
        response = self.client.post(url, {"email": "test@example.com", "password": "password"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "no_exist_user" in response.data
        del response

        # 실패: 잘못된 비밀번호로 로그인
        response = self.client.post(url, {"email": user.email, "password": "wrong_password"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "wrong_password" in response.data
        del response

        # 성공: 전화번호 로그인
        response = self.client.post(
            url,
            {"login_type": "phone_number", "phone_number": auth.number, "password": "password"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data.get("user").get("phone_number") == auth.number
        del response

        # 성공: username 로그인
        response = self.client.post(
            url,
            {"login_type": "username", "username": user.username, "password": "password"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data.get("user").get("username") == user.username
        del response

        # 성공: nickname 로그인
        response = self.client.post(
            url,
            {"login_type": "nickname", "nickname": user.nickname, "password": "password"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data.get("user").get("nickname") == user.nickname

    def test_user_detail(self):
        url = self.url_prefix + "user/detail/"

        auth: AuthOtp = AuthOtpFactory.create()
        self.client.post(
            self.url_prefix + "auth/verify_code/",
            {"number": auth.number, "otp_code": auth.otp_code}
        )
        user: User = UserFactory.create(
            phone_number=auth.number,
            otp_register_code=auth.otp_code,
            password=make_password("password")
        )
        # 실패: token 없이 내 정보를 조회하려 하는 경우
        response = self.client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "not_authenticated" in response.data

        response = self.client.post(self.url_prefix + "user/login/", {"email": user.email, "password": "password"})
        token = response.data.get("access")

        # 실패: 잘못된 token으로 내 정보를 조회하려 하는 경우
        dummy_token = token.rsplit(".")[0]
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {dummy_token}'
        )
        response = self.client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # 성공
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("user").get("email") == user.email

    def test_user_password_reset(self):
        url = self.url_prefix + "passwd/"

        number = generate_phone_number_string()
        auth: AuthOtp = AuthOtpFactory.create(
            auth_type=AuthOtpTypeEnum.EMAIL.value,
            number=number
        )
        self.client.post(
            self.url_prefix + "auth/verify_code/",
            {"number": number, "otp_code": auth.otp_code}
        )
        data = {
            "phone_number": number,
            "otp_register_code": auth.otp_code,
            "email": "email@gmail.com",
            "username": "username",
            "nickname": "nickname",
            "password": "password"
        }
        self.client.post(self.url_prefix + "user/signup/", data)

        # 실패: 전화번호 재인증 없이 비밀번호를 재설정하려는 경우
        response = self.client.post(
            url + "reset/",
            {"number": auth.number, "otp_code": 123456, "new_passwd": "new_passwd"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # 비밀번호 재설정을 위한 인증번호 요청 (passwd/request_code)
        response = self.client.post(url + "request_code/", {"number": number}, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert number == response.data.get("number")

        otp_code = response.data.get("otp_code")

        # 실패: 전화번호 인증 완료 이전에 비밀번호를 재설정하려는 경우
        response = self.client.post(
            url + "reset/",
            {"number": number, "otp_code": otp_code, "new_passwd": "new_passwd"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # 비밀번호 재설정을 위한 인증 요청 (passwd/verify_code)
        response = self.client.post(
            url + "verify_code/",
            {"number": number, "otp_code": otp_code}, format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get('number') == number

        # 성공
        response = self.client.post(
            url + "reset/",
            {"number": number, "otp_code": otp_code, "new_passwd": "new_passwd"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert number == response.data.get("number")

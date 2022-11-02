import time
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from .factories import _rand_str, generate_phone_number_string
from project.conf import app_settings


class AuthTestCase(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.url_prefix = "http://127.0.0.1:8000/auth/"

    def test_auth_send_code(self):
        url = self.url_prefix + "send_code/"

        # 성공
        number1 = generate_phone_number_string()
        response = self.client.post(url, {"number": number1})
        assert response.status_code == status.HTTP_201_CREATED

        # 실패: 올바르지 않은 전화번호에 대한 인증번호 발급 요청
        number2 = "".join(["010", _rand_str(), _rand_str()])
        response = self.client.post(url, {"number": number2})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        for data in response.data:
            if isinstance(data, dict):
                assert "invalid_number" in data.values()
            elif isinstance(data, list):
                assert "invalid_number" in data

    def test_auth_verify_code(self):
        url = self.url_prefix + "verify_code/"

        number = generate_phone_number_string()
        send_code_response = self.client.post(self.url_prefix + "send_code/", {"number": number})
        code = send_code_response.data.get('otp_code')

        # 성공
        response = self.client.post(url, {"number": number, "otp_code": code})
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get('number') == number

        # 실패: 이미 인증이 완료된 번호에 대하여 재인증을 수행하는 경우
        response = self.client.post(url, {"number": number, "otp_code": code})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid_code" in response.data

        # 실패: 올바르지 않은 전화번호에 대한 인증을 시도하는 경우
        number2 = "".join(["010", _rand_str(), _rand_str()])
        response = self.client.post(url, {"number": number2})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid_number" in response.data

        # 실패: 인증요청을 보낸적이 없는 전화번호에 대한 인증을 시도하는 경우
        response = self.client.post(url, {"number": "".join(["010", _rand_str(), _rand_str()])})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid_number" in response.data

        # 실패: 잘못된 코드로 인증을 시도하는 경우
        send_code_response = self.client.post(self.url_prefix + "send_code/", {"number": number})
        code = send_code_response.data.get('otp_code')[:-1]
        response = self.client.post(url, {"number": number, "otp_code": code})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid_code" in response.data


class ThrottlingTestCase(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.url_prefix = "http://127.0.0.1:8000/auth/"

    def test_throttling_rates(self):
        url = self.url_prefix + "send_code/"
        number = generate_phone_number_string()
        throttling_rates = app_settings.REST_FRAMEWORK_DEFAULT_THROTTLE_RATES
        num, period = throttling_rates.get('user.send_code', '5/day').split('/')

        # 성공: throttling 범위 내의 요청
        for i in range(int(num)):
            response = self.client.post(url, {"number": number})
            assert response.status_code == status.HTTP_201_CREATED

        # 실패: throttling 범위를 초과하는 요청
        response = self.client.post(url, {"number": number})
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "throttled" in response.data.values()

    def test_throttling_time_interval(self):
        # 실패: 인증이 가능한 시간을 초과한 경우
        number = generate_phone_number_string()
        send_code_response = self.client.post(self.url_prefix + "send_code/", {"number": number})
        code = send_code_response.data.get('otp_code')

        time_interval = int(app_settings.OTP_TIME_INTERVAL)
        time.sleep(time_interval)
        response = self.client.post(self.url_prefix + "verify_code/", {"number": number, "otp_code": code}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

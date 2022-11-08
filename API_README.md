## API List
[전화번호 인증번호요청](#post-usersend_code-회원가입-전에-전화번호-인증코드-요청을-보내는-경우) 
| [전화번호 인증](#put-userverify_code-전화번호-인증을-수행)
| [회원가입](#post-usersignup-사용자-회원가입) | [로그인](#post-userlogin-사용자-로그인)
| [사용자 정보 조회](#get-userdetail-사용자-정보-조회)

[비밀번호 재설정: 전화번호 인증번호 요청](#post-passwdrequest_code-비밀번호-재설정을-위한-전화번호-인증-요청)
| [비밀번호 재설정: 전화번호 인증](#put-passwdverify_code-비밀번호-재설정을-위한-전화번호-인증을-수행)
| [비밀번호 재설정](#put-passwdreset-비밀번호-재설정)

<br>

#### [POST] `/user/send_code`: 회원가입 전에 전화번호 인증코드 요청을 보내는 경우
  - Request Body Format
    ``` 
    - auth_type: string / choices=["email", "password_reset"], required=False, default="email"
      - 인증의 종류
    - number: string
      - 인증할 전화번호
    ```
  - Response Format
    ``` 
    - number: string
      - 인증할 전화번호
    - otp_code: string
      - 인증번호
    - expired_at: datetime
      - 인증번호 만료 시간 (요청으로부터 5분뒤)
    ```
  - Response Examples
    ``` json
    {
        "status": "success",
        "data": {
            "number": "010-9000-0900",
            "otp_code": "063997",
            "expired_at": "2022-11-08 11:57:04"
        }
    }
    ```
    - 잘못된 형식의 전화번호인 경우
    ``` json
    {
      "status": "fail",
      "fail_case": [
        {
          "detail": "invalid_number",
          "number_format": ["010-0000-0000"]
        }
      ]
    }
    ```
    - 하루에 보낼 수 있는 인증요청의 수를 초과한 경우 (5/day)
    ``` json
    {
      "status": "fail",
      "fail_case": {
          "detail": "throttled",
          "wait": 86084
      }
    }
    ```
    - 잘못된 인증방법인 경우
    ``` json
    {
        "status": "fail",
        "fail_case": [
            {
                "detail": "invalid_choice_test",
                "auth_type": ["email", "password_reset"]
            }
        ]
    }
    ```
------------------
#### [PUT] `/user/verify_code`: 전화번호 인증을 수행
  - Request Body Format
    ```
    - number: string
      - 인증할 전화번호
    - otp_code: string
      - 인증번호
    ```
  - Response Format
    ```
    - number: string
      - 인증할 전화번호
    - verified_at: string
      - 인증완료 시간
    ```
  - Response Examples
    ``` json
    {
      "status": "success",
      "data": {
          "number": "010-9000-9900",
          "verified_at": "2022-11-08 11:56:52"
      }
    }
    ```
    - 잘못된 형식의 전화번호인 경우
    ``` json
    {
      "status": "fail",
      "fail_case": ["invalid_number"]
    }
    ```
    - 잘못된 인증번호이거나 이미 한번 회원가입 또는 비밀번호 재설정에 사용된 인증정보인 경우 
    ``` json
    {
      "status": "fail",
      "fail_case": ["invalid_code"]
    }
    ```
------------------
#### **[POST] `/user/signup`**: 사용자 회원가입
  - Request Body Format
    ``` 
    - phone_number: string
      - 인증 완료한 전화번호
    - otp_register_code: string
      - 전화번호에 대하여 인증이 완료된 인증번호
    - email: string
      - 사용자 이메일
    - username: string
      - 사용자 이름
    - nickname: string
      - 사용자 닉네임
    - password: string
      - 사용자 비밀번호
    ```
  - Response Format
    ```
    - email: string
      - 사용자 이메일
    - username: string
      - 사용자 이름
    - nickname: string
      - 사용자 닉네임
    - phone_number: string
      - 인증 완료한 전화번호
    ```
  - Response Examples
    ``` json
    {
        "status": "success",
        "data": {
            "email": "email@gmail.com",
            "username": "username",
            "nickname": "nickname",
            "password": "password",
            "phone_number": "010-9000-9900"
        }
    }
    ```
    - 등록 또는 인증되지 않은 전화번호인 경우
    ``` json
    {
        "status": "fail",
        "fail_case": ["invalid_number"]
    }
    ```
    - 이미 회원가입에 사용된 인증정보(전화번호, 인증번호)인 경우
    - 잘못된 종류의 인증정보(회원가입/비밀번호 재설정)를 사용한 경우
    ``` json
    {
        "status": "fail",
        "fail_case": ["unauthenticated_otp"]
    }
    ```
------------------
#### **[POST] `/user/login`**: 사용자 로그인
  - Request Body Format
    ```
    - email / phone_number / username / nickname: string
      - 로그인할 고유 정보 (1가지만 입력. email이 아닌 다른 정보로 로그인하는 경우, 반드시 login_type 전달)
    - login_type: string / choices=["email", "phone_number", "username", "nickname"], required=False, default="email"
      - 로그인 방법
    - password: string
      - 비밀번호
    ```
  - Response Format
    ``` 
    - id: int
      - 사용자 id값
    - email: string
      - 사용자 이메일
    - username: string
      - 사용자 이름
    - nickname: string
      - 사용자 닉네임
    - phone_number: string
      - 사용자 전화번호
    - last_login_type: string
      - 마지막으로 로그인했던 방법
    - last_login_datetime: string
      - 마지막으로 로그인했던 시간
    ```
  - Response Examples
    ``` json
    {
        "status": "success",
        "data": {
            "user": {
                "id": 1,
                "email": "email@gmail.com",
                "username": "username",
                "nickname": "nickname",
                "phone_number": "010-9000-9900",
                "is_staff": false,
                "last_login_type": "email",
                "last_login_datetime": null
            },
            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..",
            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.."
        }
    }
    ```
    - 잘못된 `login_type`값을 전달한 경우
    ``` json
    {
        "status": "fail",
        "fail_case": [
            {
                "detail": "invalid_choice_[value]",
                "login_type": ["email", "phone_number", "username", "nickname"]
            }
        ]
    }
    ```
    - 잘못된 계정정보를 입력한 경우
    ``` json
    {
        "status": "fail",
        "fail_case": ["no_exist_user"]
    }
    ```
    - 잘못된 비밀번호를 입력한 경우
    ``` json
    {
        "status": "fail",
        "fail_case": ["wrong_password"]
    }
    ```
------------------
#### **[GET] `/user/detail`**: 사용자 정보 조회
  - Request Header
    ```
    Authorization: Bearer {Token}
    ```
  - Response Format
    ```
    - id: int
      - 사용자 id값
    - email: string
      - 사용자 이메일
    - username: string
      - 사용자 이름
    - nickname: string
      - 사용자 닉네임
    - phone_number: string
      - 사용자 전화번호
    - last_login_type: string
      - 마지막으로 로그인했던 방법
    - last_login_datetime: string
      - 마지막으로 로그인했던 시간
    ```
  - Response Examples
    ``` json
    {
        "status": "success",
        "data": {
            "user": {
                "id": 1,
                "email": "email@gmail.com",
                "username": "username",
                "nickname": "nickname",
                "phone_number": "010-9000-9900",
                "is_staff": false,
                "last_login_type": "email",
                "last_login_datetime": null
            }
        }
    }
    ```
    - Token값이 없거나 유효하지 않은 Token을 전달한 경우
    ``` json
    {
        "status": "fail",
        "fail_case": ["not_authenticated"]
    }
    ```
------------------
#### **[POST] `/passwd/request_code`**: 비밀번호 재설정을 위한 전화번호 인증 요청
  - Request Body Format
    ```
    - auth_type: string / choices=["email", "password_reset"], required=False, default="password_reset"
      - 인증의 종류
    - number: string
      - 인증할 전화번호
    ```
  - Response Format
    ```
    - number: string
      - 인증할 전화번호
    - otp_code: string
      - 인증번호
    - expired_at: datetime
      - 인증번호 만료 시간 (요청으로부터 5분뒤)
    ```
  - Response Examples
    ``` json
    {
        "status": "success",
        "data": {
            "number": "010-9000-0900",
            "otp_code": "063997",
            "expired_at": "2022-11-08 11:57:04"
        }
    }
    ```
    - 잘못된 형식의 전화번호인 경우
    ``` json
    {
      "status": "fail",
      "fail_case": [
        {
          "detail": "invalid_number",
          "number_format": ["010-0000-0000"]
        }
      ]
    }
    ```
    - 하루에 보낼 수 있는 인증요청의 수를 초과한 경우 (5/day)
    ``` json
    {
      "status": "fail",
      "fail_case": {
          "detail": "throttled",
          "wait": 86084
      }
    }
    ```
    - 잘못된 인증방법인 경우
    ``` json
    {
        "status": "fail",
        "fail_case": [
            {
                "detail": "invalid_choice_test",
                "auth_type": ["email", "password_reset"]
            }
        ]
    }
    ```
------------------
#### **[PUT] `/passwd/verify_code`**: 비밀번호 재설정을 위한 전화번호 인증을 수행
  - Request Body Format
    ```
    - number: string
      - 인증할 전화번호
    - otp_code: string
      - 인증번호
    ```
  - Response Format
    ```
    - number: string
      - 인증할 전화번호
    - verified_at: string
      - 인증완료 시간
    ```
  - Response Examples
    ``` json
    {
      "status": "success",
      "data": {
          "number": "010-9000-9900",
          "verified_at": "2022-11-08 11:56:52"
      }
    }
    ```
    - 잘못된 형식의 전화번호인 경우
    ``` json
    {
      "status": "fail",
      "fail_case": ["invalid_number"]
    }
    ```
    - 잘못된 인증번호이거나 이미 한번 비밀번호 재설정 또는 회원가입에 사용된 인증정보인 경우 
    ``` json
    {
      "status": "fail",
      "fail_case": ["invalid_code"]
    }
    ```
------------------
#### **[PUT] `/passwd/reset/`**: 비밀번호 재설정
  - Request Body Format
    ```
    - phone_number: string
      - 인증 완료한 전화번호
    - otp_register_code: string
      - 전화번호에 대하여 인증이 완료된 인증번호
    - new_passwd: string
      - 변경할 비밀번호
    ```
  - Response Format
    ```
    - number: string
      - 사용자 비밀번호
    - new_passwd: string
      - 새로 설정한 비밀번호
    ```
  - Response Examples
    ``` json
    {
        "status": "success",
        "data": {
            "number": "010-9000-9900",
            "new_passwd": "new_passwd"
        }
    }
    ```
    - 잘못된 인증 전화번호 또는 코드를 입력한 경우
    ``` json
    {
      "status": "fail",
      "fail_case": ["invalid_number_or_code"]
    }
    ```
    - 이미 비밀번호 재설정에 한번 이상 사용된 인증정보인 경우
    ``` json
    {
      "status": "fail",
      "fail_case": ["invalid_auth_otp_data"]
    }
    ```
    - 해당 전화번호로 가입된 사용자가 없는 경우
    ``` json
    {
      "status": "fail",
      "fail_case": ["no_exist_user"]
    }
    ```
    - 직전에 사용했던 비밀번호와 동일한 비밀번호를 입력한 경우
    ``` json
    {
        "status": "fail",
        "fail_case": ["previous_passwd"]
    }
    ```
import math

from rest_framework.exceptions import (
    Throttled as BaseThrottled,
    NotAuthenticated as BaseNotAuthenticated,
    PermissionDenied as BasePermissionDenied
)


class Throttled(BaseThrottled):
    default_detail = "throttled"

    def __init__(self, wait=None, detail=None, code=None):
        if code is None:
            code = self.default_code
        if wait is not None:
            wait = math.ceil(wait)
            detail = detail or self.default_detail
        self.wait = wait
        self.detail = {"detail": detail, "wait": wait}


class NotAuthenticated(BaseNotAuthenticated):
    default_detail = "not_authenticated"


class PermissionDenied(BasePermissionDenied):
    default_detail = "permission_denied"

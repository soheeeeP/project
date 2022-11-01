import math

from rest_framework.exceptions import Throttled


class BaseThrottled(Throttled):
    default_detail = "throttled"

    def __init__(self, wait=None, detail=None, code=None):
        if code is None:
            code = self.default_code
        if wait is not None:
            wait = math.ceil(wait)
            detail = detail or self.default_detail
        self.wait = wait
        self.detail = {"detail": detail, "wait": wait}

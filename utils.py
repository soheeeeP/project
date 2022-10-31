import json
from rest_framework import renderers
from rest_framework.status import is_success, is_client_error, is_server_error


def set_response_key(code: int) -> tuple[str, str]:
    status, data = 'undefined', 'message'
    if is_success(code):
        return 'success', 'data'
    elif is_client_error(code):
        return 'fail', 'fail_case'
    elif is_server_error(code):
        return 'error', 'message'
    return status, data


class ResponseRenderer(renderers.JSONRenderer):
    charset = 'utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get('response')
        status, data_key = set_response_key(response.status_code)
        return json.dumps({"status": status, data_key: data})

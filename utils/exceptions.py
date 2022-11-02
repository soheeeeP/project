from rest_framework.exceptions import Throttled
from rest_framework.views import exception_handler


def get_error_details(data):
    if isinstance(data, (list, tuple)):
        return [get_error_details(item) if isinstance(item, dict) else str(item) for item in data]
    elif isinstance(data, dict):
        return {
            key: get_error_details(value)
            for key, value in data.items()
        }
    return str(data)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if isinstance(exc, Throttled):
        response.data = exc.detail
        return response

    details, data = get_error_details(exc.detail), []
    if isinstance(details, dict):
        for key, value in details.items():
            if isinstance(value, (list, tuple)):
                data.extend(value)
            elif isinstance(value, dict):
                data.append(value)
    elif isinstance(details, list):
        data = details
    else:
        data = [details]
    response.data = data
    return response

from rest_framework.views import exception_handler


def get_error_details(data):
    if isinstance(data, (list, tuple)):
        return [str(item) for item in data]
    elif isinstance(data, dict):
        return {
            key: get_error_details(value)
            for key, value in data.items()
        }
    return data


def custom_exception_handler(exc, context):
    details, data = get_error_details(exc.detail), []
    for key, value in details.items():
        if isinstance(value, (list, tuple)):
            data.extend(value)
        elif isinstance(value, dict):
            data.append(value)
    response = exception_handler(exc, context)
    response.data = data
    return response

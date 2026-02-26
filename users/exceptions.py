from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework import status


def success_response(data=None, message="Success", status_code=status.HTTP_200_OK):
    return Response({
        "success": True,
        "message": message,
        "data": data or {}
    }, status=status_code)


def error_response(message="An error occurred", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    return Response({
        "success": False,
        "message": message,
        "errors": errors or {}
    }, status=status_code)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            "success": False,
            "message": _extract_message(response.data),
            "errors": response.data
        }

    return response


def _extract_message(data):
    if isinstance(data, dict):
        if 'detail' in data:
            return str(data['detail'])
        for key, val in data.items():
            if isinstance(val, list) and val:
                return f"{key}: {val[0]}"
    if isinstance(data, list) and data:
        return str(data[0])
    return "Request failed"
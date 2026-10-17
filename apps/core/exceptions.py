from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Centralized exception handler for Zecpath APIs.
    """

    response = exception_handler(exc, context)

    if response is not None:

        status_code = response.status_code

        if status_code == status.HTTP_400_BAD_REQUEST:
            error_type = "Bad Request"

        elif status_code == status.HTTP_401_UNAUTHORIZED:
            error_type = "Unauthorized"

        elif status_code == status.HTTP_403_FORBIDDEN:
            error_type = "Forbidden"

        elif status_code == status.HTTP_404_NOT_FOUND:
            error_type = "Not Found"

        elif status_code >= 500:
            error_type = "Server Error"

        else:
            error_type = "API Error"

        return Response(
            {
                "success": False,
                "status_code": status_code,
                "error": error_type,
                "details": response.data,
            },
            status=status_code
        )

    # Handles unexpected exceptions
    return Response(
        {
            "success": False,
            "status_code": 500,
            "error": "Server Error",
            "details": "An unexpected error occurred.",
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Allows access only to users with the Admin role.
    """

    message = "Admin access required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )


class IsEmployer(BasePermission):
    """
    Allows access only to users with the Employer role.
    """

    message = "Employer access required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "employer"
        )


class IsCandidate(BasePermission):
    """
    Allows access only to users with the Candidate role.
    """

    message = "Candidate access required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "candidate"
        )


class IsAdminOrEmployer(BasePermission):
    """
    Allows access to Admin and Employer users.
    """

    message = "Admin or Employer access required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["admin", "employer"]
        )
from rest_framework.permissions import BasePermission


class IsCandidateProfileOwner(BasePermission):

    message = "Candidate access required."

    def has_permission(self, request, view):

        user = request.user

        return (
            user.is_authenticated
            and user.role in ["candidate", "admin"]
        )


class IsEmployerProfileOwner(BasePermission):

    message = "Employer access required."

    def has_permission(self, request, view):

        user = request.user

        return (
            user.is_authenticated
            and user.role in ["employer", "admin"]
        )
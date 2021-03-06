from rest_framework.permissions import BasePermission


class IsAdministratorPermission(BasePermission):

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin


class IsModeratorPermission(BasePermission):

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_moderator

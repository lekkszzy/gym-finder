from rest_framework import permissions

# Both classes adapted from https://www.django-rest-framework.org/api-guide/permissions/#examples


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Instance must have an attribute named `owner`.
        return obj.owner == request.user


class ReadOnly(permissions.BasePermission):
    """
    Allows read-only requests (GET, HEAD, OPTIONS) for everyone.
    """

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS
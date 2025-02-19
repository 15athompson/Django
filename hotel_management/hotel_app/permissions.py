from rest_framework.permissions import BasePermission

class IsStaff(BasePermission):
    """Custom permission to only allow staff users."""
    def has_permission(self, request, view):
        return request.user and request.user.is_staff

class IsManager(BasePermission):
    """Custom permission to only allow managers."""
    def has_permission(self, request, view):
        return request.user and request.user.userprofile.role.name == 'manager'

class IsReceptionist(BasePermission):
    """Custom permission to only allow receptionists."""
    def has_permission(self, request, view):
        return request.user and request.user.userprofile.role.name == 'reception'

class IsHousekeeping(BasePermission):
    """Custom permission to only allow housekeeping staff."""
    def has_permission(self, request, view):
        return request.user and request.user.userprofile.role.name == 'housekeeping'

class IsMaintenance(BasePermission):
    """Custom permission to only allow maintenance staff."""
    def has_permission(self, request, view):
        return request.user and request.user.userprofile.role.name == 'maintenance'

class IsAuthenticated(BasePermission):
    """Custom permission to only allow authenticated users."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

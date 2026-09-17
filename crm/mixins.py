from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied

from .constants import ROLE_ADMIN, ROLE_DIRECTOR, ROLE_MANAGER
from .utils import user_has_role


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    allowed_roles = []

    def test_func(self):
        return user_has_role(self.request.user, *self.allowed_roles)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied('Недостаточно прав для выполнения операции.')
        return super().handle_no_permission()


class BusinessReadMixin(RoleRequiredMixin):
    allowed_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_DIRECTOR]


class BusinessWriteMixin(RoleRequiredMixin):
    allowed_roles = [ROLE_ADMIN, ROLE_MANAGER]


class AdminOnlyMixin(RoleRequiredMixin):
    allowed_roles = [ROLE_ADMIN]

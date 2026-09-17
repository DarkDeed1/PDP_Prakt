from urllib.parse import urlencode

from django.contrib.auth.models import Group

from .constants import DEAL_STATUS_CHOICES, ROLE_ADMIN, ROLE_CHOICES
from .models import AuditLog, DealStatusHistory


def ensure_roles_exist():
    for role in ROLE_CHOICES:
        Group.objects.get_or_create(name=role)


def get_user_role(user):
    if not getattr(user, 'is_authenticated', False):
        return ''
    group = user.groups.first()
    return group.name if group else ''


def user_has_role(user, *roles):
    if not getattr(user, 'is_authenticated', False):
        return False
    if user.is_superuser:
        return True
    return get_user_role(user) in roles


def get_client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def write_audit_log(request, action, obj=None, details=''):
    object_id = getattr(obj, 'pk', None) if obj else None
    object_repr = str(obj) if obj else 'Системное действие'
    model_name = obj._meta.verbose_name if obj else 'Система'
    AuditLog.objects.create(
        user=request.user if getattr(request, 'user', None) and request.user.is_authenticated else None,
        action=action,
        model_name=model_name,
        object_id=object_id,
        object_repr=object_repr,
        details=details,
        ip_address=get_client_ip(request),
    )


def create_status_history(deal, old_status, new_status, user, comment=''):
    if old_status == new_status and old_status:
        return
    DealStatusHistory.objects.create(
        deal=deal,
        old_status=old_status or '',
        new_status=new_status,
        changed_by=user,
        comment=comment,
    )


def status_display_map():
    return dict(DEAL_STATUS_CHOICES)


def build_querystring(params, **updates):
    data = params.copy()
    for key, value in updates.items():
        if value in [None, '']:
            data.pop(key, None)
        else:
            data[key] = value
    return urlencode(data, doseq=True)

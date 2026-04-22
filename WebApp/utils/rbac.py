from functools import wraps
from flask import abort, current_app
from flask_login import current_user

"""
Simple RBAC utilities: role-based decorator and permission checks.

This module centralizes role <-> permission mappings and provides two
decorators:
- `roles_required(*roles)` : restricts access to one of the provided roles
- `permission_required(permission)` : checks a named permission via mapping

Usage:
    @roles_required(Role.receptionist, Role.admin)
    def some_view():
        ...

    @permission_required('create_booking')
    def create_booking():
        ...

The `ROLE_PERMISSIONS` mapping can be extended to add fine-grained
permission checks without touching route code.
"""


def _role_name(role_or_str):
    # Accept either Enum members (Role.x) or strings
    try:
        return role_or_str.name
    except Exception:
        return str(role_or_str)


# Default permission set — adjust as application grows.
ROLE_PERMISSIONS = {
    # names used to compare with `current_user.role.name`
}


def init_role_permissions(mapping):
    """Optional runtime initializer to override or extend permissions."""
    ROLE_PERMISSIONS.clear()
    for k, v in mapping.items():
        ROLE_PERMISSIONS[_role_name(k)] = set(v)


def roles_required(*allowed_roles):
    """Decorator to require one of the provided roles.

    allowed_roles may be Role enum members or strings.
    """

    allowed_names = {_role_name(r) for r in allowed_roles}

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            user_role = getattr(current_user.role, "name", str(current_user.role))
            if user_role not in allowed_names:
                current_app.logger.debug(
                    "Access denied for user=%s role=%s allowed=%s",
                    getattr(current_user, "username", None),
                    user_role,
                    allowed_names,
                )
                abort(403)
            return f(*args, **kwargs)

        return wrapped

    return decorator


def permission_required(permission):
    """Decorator that checks if current_user has the named permission.

    Looks up the permission in `ROLE_PERMISSIONS` for the user's role.
    """

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            role_name = getattr(current_user.role, "name", str(current_user.role))
            perms = ROLE_PERMISSIONS.get(role_name, set())
            # First check static mapping
            if permission in perms:
                return f(*args, **kwargs)

            # Then try DB-backed RolePermission if available
            try:
                from ..models import RolePermission

                # Query for explicit role-permission mapping
                from .. import db

                rp = db.session.execute(
                    db.select(RolePermission).filter_by(
                        role_name=role_name, permission=permission
                    )
                ).scalar_one_or_none()
                if rp is not None:
                    return f(*args, **kwargs)
            except Exception:
                # If DB or model not available, fall through to deny
                pass

            # Deny if neither static nor DB mapping grants permission
            if permission not in perms:
                current_app.logger.debug(
                    "Permission denied user=%s role=%s permission=%s",
                    getattr(current_user, "username", None),
                    role_name,
                    permission,
                )
                abort(403)
            return f(*args, **kwargs)

        return wrapped

    return decorator


# Initialize a sensible default mapping using simple string role names.
def _default_mapping():
    return {
        "receptionist": [
            "view_bookings",
            "create_booking",
            "modify_booking",
            "check_in",
            "check_out",
            "view_rooms",
            "assign_room",
        ],
        "admin": [
            # admin has everything receptionist has plus admin actions
            "view_bookings",
            "create_booking",
            "modify_booking",
            "check_in",
            "check_out",
            "view_rooms",
            "assign_room",
            "accept_reject_booking",
            "delete_booking",
            "manage_rooms",
            "manage_users",
            "manage_system",
        ],
    }


init_role_permissions(_default_mapping())

import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from WebApp import create_app, db
from WebApp.models import Permission, RolePermission
from WebApp.utils.rbac import ROLE_PERMISSIONS

app = create_app()
with app.app_context():
    all_perms = set()
    for perms in ROLE_PERMISSIONS.values():
        all_perms.update(perms)

    created_perms = []
    for p in sorted(all_perms):
        existing = Permission.query.filter_by(name=p).first()
        if not existing:
            perm = Permission(name=p, description=None)
            db.session.add(perm)
            created_perms.append(p)
    db.session.commit()

    created_rp = []
    for role_name, perms in ROLE_PERMISSIONS.items():
        for p in perms:
            exists = RolePermission.query.filter_by(role_name=role_name, permission=p).first()
            if not exists:
                rp = RolePermission(role_name=role_name, permission=p)
                db.session.add(rp)
                created_rp.append((role_name, p))
    db.session.commit()

    print('Permissions created:', created_perms)
    print('RolePermissions created:', created_rp)
    print('Total permissions in DB:', Permission.query.count())
    print('Total role_permissions in DB:', RolePermission.query.count())

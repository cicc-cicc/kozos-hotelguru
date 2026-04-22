import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from WebApp import create_app, db
from WebApp.models import User, Role
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    username = 'admin_janos'
    password = 'admin123'
    user = User.query.filter_by(username=username).first()
    if user:
        print('Admin user exists. Updating password to default (admin123).')
        user.password_hash = generate_password_hash(password)
        user.role = Role.admin
        db.session.commit()
        print('Updated.')
    else:
        print('Creating admin user...')
        new_user = User(
            username=username,
            email='admin@hotelguru.hu',
            password_hash=generate_password_hash(password),
            phone='+36-30-111-2222',
            address='Budapest, Fő utca 1',
            role=Role.admin,
        )
        db.session.add(new_user)
        db.session.commit()
        print('Admin created with password admin123')

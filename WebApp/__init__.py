from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager # 1. Új import
from flask_wtf import CSRFProtect
try:
    from flasgger import Swagger
except Exception:
    Swagger = None
from flask_jwt_extended import JWTManager


# Globális objektumok
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager() # 2. LoginManager inicializálása
csrf = CSRFProtect()
jwt = JWTManager()
if Swagger is not None:
    swagger = Swagger()
else:
    swagger = None

def create_app():
    app = Flask(__name__)
    # Allow overriding the database via environment variable for CI/tests/local overrides
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        from .config import db_config
        params = db_config()
        app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'hotelguru_titok'

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    # Flasgger (OpenAPI / Swagger) init
    if swagger is not None:
        try:
            swagger.init_app(app)
        except Exception:
            # If Flasgger is installed but incompatible, skip initialization
            pass
    # JWT init
    app.config.setdefault('JWT_SECRET_KEY', app.config.get('SECRET_KEY'))
    jwt.init_app(app)
    
    # 3. Flask-Login beállítása az app-hoz
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login' # Ide irányít, ha valaki bejelentkezés nélkül próbál védett oldalt (pl. profilt) megnyitni
    login_manager.login_message = 'Kérjük, jelentkezzen be az oldal eléréséhez.'
    login_manager.login_message_category = 'warning'

    with app.app_context():
        from . import models
        
        # 4. User_loader funkció definiálása a Flask-Login számára
        @login_manager.user_loader
        def load_user(user_id):
            return models.User.query.get(int(user_id))
            
        # 5. Blueprintek regisztrálása
        from .routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth') # Minden auth route kap egy /auth előtagot (pl. /auth/login)
        
        from .routes.guests_routes import guest_bp
        app.register_blueprint(guest_bp) # Vendég útvonalak a gyökerére kerülnek (pl. /search-results) 
        # Az alap útvonalak megtartása (ha maradnak a routes.py-ban)
        #from .routes import routes


        from .routes.reception_routes import reception_bp
        app.register_blueprint(reception_bp, url_prefix='/reception') # Recepciós útvonalak /reception előtaggal (pl. /reception/dashboard)



        from .routes.admin_routes import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin') # Admin útvonalak /admin előtaggal (pl. /admin/dashboard)
        
        # API blueprint (JSON endpoints + OpenAPI)
        from .routes.api import api_bp
        app.register_blueprint(api_bp, url_prefix='/api')
    return app

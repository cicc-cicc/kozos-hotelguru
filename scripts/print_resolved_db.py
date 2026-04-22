import os
from WebApp import create_app

print('DATABASE_URL env var:', os.environ.get('DATABASE_URL'))
app = create_app()
print('Resolved SQLALCHEMY_DATABASE_URI:', app.config.get('SQLALCHEMY_DATABASE_URI'))

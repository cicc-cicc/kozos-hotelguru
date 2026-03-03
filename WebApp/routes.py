from flask import render_template
from . import db
from .models import Room
from flask import current_app as app

@app.route('/')
def index(): #minden szobát lekér az adatbázisból
    rooms = Room.query.all()
    return render_template('rooms.html', rooms=rooms)

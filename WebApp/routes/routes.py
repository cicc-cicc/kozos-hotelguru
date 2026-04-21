from flask import render_template
from flask import current_app as app
from .models import Room


@app.route("/")
def index():
    rooms = Room.query.all()
    return render_template("rooms.html", rooms=rooms)

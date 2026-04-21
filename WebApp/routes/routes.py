from flask import render_template, redirect, url_for, flash, request
from flask import current_app as app
from . import db
from .models import Booking, ExtraService, Room, BookingService, User
from .forms.reception_forms import ServiceOrderForm
from .forms.login_forms import LoginForm


@app.route("/")
def index():
    rooms = Room.query.all()
    return render_template("rooms.html", rooms=rooms)

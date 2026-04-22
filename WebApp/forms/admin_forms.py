from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    IntegerField,
    FloatField,
    TextAreaField,
    SubmitField,
    SelectField,
)
from wtforms.validators import DataRequired, NumberRange
from ..models import RoomStatus


class RoomForm(FlaskForm):
    # szoba felvételezése és szerkesztése adminisztrátoroknak
    room_number = StringField("Szobaszám", validators=[DataRequired()])
    capacity = IntegerField("Férőhely", validators=[DataRequired(), NumberRange(min=1)])
    price_per_night = FloatField("Ár / éjszaka (Ft)", validators=[DataRequired()])
    equipment = TextAreaField("Felszereltség (vesszővel elválasztva)")
    description = TextAreaField("Leírás")
    status = SelectField(
        "Status",
        choices=[(status.name, status.value) for status in RoomStatus],
        validators=[DataRequired()],
    )

    submit = SubmitField("Mentés")


class RoomDeleteForm(FlaskForm):
    # megerősítést kér a szoba törléséhez
    submit = SubmitField("Végleges törlés")


class UserRoleForm(FlaskForm):
    role = SelectField("Szerepkör", choices=[('guest','guest'), ('receptionist','receptionist'), ('admin','admin')], validators=[DataRequired()])
    submit = SubmitField("Mentés")


class PermissionForm(FlaskForm):
    name = StringField("Permission név", validators=[DataRequired()])
    description = TextAreaField("Leírás")
    submit = SubmitField("Mentés")

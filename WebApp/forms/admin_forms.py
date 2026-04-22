from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    IntegerField,
    FloatField,
    TextAreaField,
    SubmitField,
    SelectField,
    HiddenField,
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


class ServiceDeleteForm(FlaskForm):
    submit = SubmitField("Töröl")


class UserRoleForm(FlaskForm):
    role = SelectField("Szerepkör", choices=[('guest','guest'), ('receptionist','receptionist'), ('admin','admin')], validators=[DataRequired()])
    submit = SubmitField("Mentés")


class PermissionForm(FlaskForm):
    name = StringField("Permission név", validators=[DataRequired()])
    description = TextAreaField("Leírás")
    submit = SubmitField("Mentés")


class AdminServiceForm(FlaskForm):
    booking_id = SelectField("Foglalás", coerce=int, validators=[DataRequired()])
    service_id = SelectField("Szolgáltatás", coerce=int, validators=[DataRequired()])
    quantity = IntegerField("Mennyiség", default=1, validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField("Hozzáad");


class AdminCreateServiceForm(FlaskForm):
    name = StringField("Név", validators=[DataRequired()])
    description = TextAreaField("Leírás")
    price = FloatField("Ár (Ft)", validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField("Szolgáltatás létrehozása")


class BookingServiceAddForm(FlaskForm):
    booking_id = HiddenField("Foglalás", validators=[DataRequired()])
    service_id = SelectField("Szolgáltatás", coerce=int, validators=[DataRequired()])
    quantity = IntegerField("Mennyiség", default=1, validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField("Hozzáad")

    def __init__(self, *args, **kwargs):
        super(BookingServiceAddForm, self).__init__(*args, **kwargs)
        from ..models import ExtraService
        services = ExtraService.query.order_by(ExtraService.name).all()
        self.service_id.choices = [(s.id, f"{s.name} ({int(s.price)} Ft)") for s in services]

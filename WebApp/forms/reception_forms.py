from flask_wtf import FlaskForm
from wtforms import SubmitField, HiddenField, SelectField, IntegerField
from wtforms.validators import DataRequired, NumberRange
from ..models import ExtraService  # Importáljuk a modellt a dinamikus lekérdezéshez


class BookingActionForm(FlaskForm):
    # foglalások kezelése
    # booking_id is provided in the URL and via hidden input in the template.
    # Make it optional for validation to avoid issues when rendering multiple
    # forms on the same page (each form creates identical field names).
    booking_id = HiddenField("Booking ID")

    # recepciós kiválaszthatja a műveletet
    action = SelectField(
        "Művelet",
        choices=[
            ("confirm", "Visszaigazolás (Confirm)"),
            ("check_in", "Bejelentkeztetés (Check-in)"),
            ("check_out", "Kijelentkeztetés és Számlázás (Check-out)"),
            ("cancel", "Foglalás lemondása"),
        ],
        validators=[DataRequired()],
    )

    submit = SubmitField("Végrehajtás")


class ServiceOrderForm(FlaskForm):
    # Kiegészítő szolgáltatások megrendelése a foglaláshoz
    booking_id = HiddenField("Booking ID", validators=[DataRequired()])

    # coerce=int nagyon fontos, mert az ExtraService ID-ját (számot) akarjuk visszakapni
    service_id = SelectField("Szolgáltatás", coerce=int, validators=[DataRequired()])

    quantity = IntegerField(
        "Mennyiség", default=1, validators=[DataRequired(), NumberRange(min=1)]
    )

    submit = SubmitField("Hozzáadás a számlához")

    def __init__(self, *args, **kwargs):
        super(ServiceOrderForm, self).__init__(*args, **kwargs)
        # Automatikus, dinamikus feltöltés az adatbázisból minden példányosításkor
        services = ExtraService.query.all()
        self.service_id.choices = [
            (service.id, f"{service.description or service.name} ({service.price} Ft)")
            for service in services
        ]

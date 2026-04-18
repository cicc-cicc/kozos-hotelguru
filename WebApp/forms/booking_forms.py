from flask_wtf import FlaskForm
from wtforms import DateField, SubmitField, HiddenField, IntegerField, BooleanField
from wtforms.validators import DataRequired, NumberRange
from datetime import date
from wtforms import Form, validators

class RoomSearchForm(FlaskForm):
    #űrlap a szabad szobák kereséséhez, a vendégek használják a főoldalon
    arrival_date = DateField('Érkezés napja', 
                             format='%Y-%m-%d',
                             default=date.today,
                             validators=[DataRequired(message="Kérjük, adja meg az érkezés dátumát!")])

    departure_date = DateField('Távozás napja', 
                               format='%Y-%m-%d',
                               validators=[DataRequired(message="Kérjük, adja meg a távozás dátumát!")])
    guests = IntegerField('Vendégek száma', 
                          validators=[DataRequired(message="Kérjük, adja meg a vendégek számát!"), NumberRange(min=1, message="Legalább egy vendégnek kell lennie!")])
    submit = SubmitField('Szabad szobák keresése')


    def validate(self, **kwargs):
            # Az alapértelmezett validáció futtatása (és a paraméterek továbbadása)
            if not super().validate(**kwargs):
                return False
                
            # Dátumok ellenőrzése, de csak ha már mindkettő ki van töltve
            if self.arrival_date.data and self.departure_date.data:
                if self.departure_date.data <= self.arrival_date.data:
                    self.departure_date.errors.append("A távozás dátuma későbbi kell legyen, mint az érkezés dátuma.")
                    return False
                    
            return True

class BookingRequestForm(FlaskForm):
    #űrlap a foglalás véglegesítéséhez
    #a szoba ID-ját rejtett mezőben tároljuk, hogy tudjuk, melyik szobát foglalják
    room_id = HiddenField('Room ID', validators=[DataRequired()])
    arrival_date = HiddenField('Arrival Date', validators=[DataRequired()])
    departure_date = HiddenField('Departure Date', validators=[DataRequired()])
    
    submit = SubmitField('Foglalás véglegesítése')

class BookingCancelForm(FlaskForm):
    confirm = BooleanField('Biztosan lemondod a foglalást?', validators=[DataRequired()])
    submit = SubmitField('Foglalás lemondása')


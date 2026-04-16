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
    
    def validate(self):
        if not super().validate():
            return False
        if self.departure_date.data < self.arrival_date.data:
            self.departure_date.errors.append("A távozás dátuma nem lehet korábbi, mint az érkezés dátuma.")
            return False
        return True

    guests = IntegerField('Vendégek száma', 
                          default=1,
                          validators=[DataRequired(), NumberRange(min=1, max=10)])
    
    submit = SubmitField('Szabad szobák keresése')

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


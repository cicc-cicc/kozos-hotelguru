from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError

class LoginForm(FlaskForm):
    username = StringField('Felhasználónév', 
                           validators=[DataRequired(message="Kérjük, adja meg a felhasználónevét!")])
    password = PasswordField('Jelszó', 
                             validators=[DataRequired(message="Kérjük, adja meg a jelszavát!")])
    remember = BooleanField('Emlékezz rám')
    submit = SubmitField('Bejelentkezés')

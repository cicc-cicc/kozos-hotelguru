from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp
import re

def validate_password_strength(form, field):
    value = field.data or ''
    if len(value) < 8:
        raise ValidationError('A jelszónak legalább 8 karakter hosszúnak kell lennie.')
    if not re.search(r'[A-Z]', value):
        raise ValidationError('A jelszónak tartalmaznia kell legalább egy nagybetűt.')
    if not re.search(r'[a-z]', value):
        raise ValidationError('A jelszónak tartalmaznia kell legalább egy kisbetűt.')
    if not re.search(r'\d', value):
        raise ValidationError('A jelszónak tartalmaznia kell legalább egy számot.')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        raise ValidationError('A jelszónak tartalmaznia kell legalább egy speciális karaktert.')

def validate_email_domain(form, field):
    allowed_domains = ['gmail.com', 'yahoo.com', 'outlook.com']  # tetszőleges lista
    email = (field.data or '').strip()
    if '@' in email:
        domain = email.split('@')[-1].lower()
        if domain not in allowed_domains:
            raise ValidationError(f'Az email domain ({domain}) nem engedélyezett.')
    else:
        raise ValidationError('Érvénytelen e-mail cím.')

class RegistrationForm(FlaskForm):
    username = StringField('Felhasználónév', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('E-mail cím', validators=[DataRequired(), Email(message="Érvénytelen e-mail cím!"), validate_email_domain])
    password = PasswordField('Jelszó', validators=[DataRequired(), Length(min=8), validate_password_strength])
    confirm_password = PasswordField('Jelszó ismét', validators=[DataRequired(), EqualTo('password', message="A jelszavaknak egyezniük kell!")])
        
    # személyes adatok
    phone = StringField('Telefonszám', validators=[DataRequired(), Regexp(r'^\+36\d{9}$', message='Telefonszám formátuma érvénytelen: +36-val kell kezdődnie, majd 9 számjegy.')])
    address = StringField('Lakcím', validators=[DataRequired(message="A számlázáshoz kötelező megadni!")])
        
    submit = SubmitField('Regisztráció')

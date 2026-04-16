from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Regexp

class UserProfileForm(FlaskForm):
    #vendég adatok módosítása a profil oldalon
    email = StringField('E-mail cím', 
                        validators=[DataRequired(), Email(message="Érvénytelen e-mail formátum!")])
    
    phone = StringField('Phone', validators=[DataRequired(), Regexp(r'^\+36\d{9,10}$', message='Telefonszám formátuma érvénytelen: +36-val kell kezdődnie, majd 9-10 számjegy.')])
    
    address = StringField('Lakcím', 
                          validators=[DataRequired(), Length(max=255)])
    
    submit = SubmitField('Profil frissítése')


    
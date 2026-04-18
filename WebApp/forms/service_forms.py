from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, HiddenField, IntegerField
from wtforms.validators import DataRequired, NumberRange
from ..models import ExtraService

class GuestServiceOrderForm(FlaskForm):
    quantity = IntegerField('Mennyiség', validators=[DataRequired(), NumberRange(min=1)])
    booking_id = HiddenField('Booking ID', validators=[DataRequired()])
    
    service_id = SelectField('Válasszon szolgáltatást', coerce=int, validators=[DataRequired()])
    
    submit = SubmitField('Megrendelés')

    def __init__(self, *args, **kwargs):
        super(GuestServiceOrderForm, self).__init__(*args, **kwargs)
        
        services = ExtraService.query.all()
        
        self.service_id.choices = [
            (service.id, f"{service.description or service.name} ({service.price} Ft)") 
            for service in services
        ]

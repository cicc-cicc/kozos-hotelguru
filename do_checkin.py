from WebApp import create_app
from WebApp.models import Booking
from WebApp.services.reception_service import perform_booking_action

app = create_app()
with app.app_context():
    b = Booking.query.filter_by(id=2).first()
    print("Before:", b.id, b.status, b.status.value)
    perform_booking_action(b, "check_in")
    b2 = Booking.query.get(2)
    print("After:", b2.id, b2.status, b2.status.value)

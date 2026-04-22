from WebApp import create_app
from WebApp.models import Booking

app = create_app()
with app.app_context():
    for b in Booking.query.order_by(Booking.id).all():
        print(b.id, b.user.username, b.room.room_number, b.status, b.status.value)

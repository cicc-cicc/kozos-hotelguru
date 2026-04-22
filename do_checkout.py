from WebApp import create_app
from WebApp.models import Booking, AuditLog
from WebApp.services.reception_service import perform_booking_action

app = create_app()
with app.app_context():
    b = Booking.query.filter_by(id=2).first()
    print("Before:", b.id, b.status, b.check_in_time, b.check_out_time, b.room.status)
    perform_booking_action(b, "check_out")
    b2 = Booking.query.get(2)
    print(
        "After:", b2.id, b2.status, b2.check_in_time, b2.check_out_time, b2.room.status
    )

    logs = AuditLog.query.filter_by(booking_id=2).order_by(AuditLog.created_at).all()
    for log in logs:
        print("LOG:", log.action, log.user_id, log.created_at, log.details)

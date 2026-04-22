from WebApp import create_app, db
from WebApp.models import Booking, BookingStatus

app = create_app()

with app.app_context():
    # Use test client to login and perform action
    client = app.test_client()

    # Login as receptionist
    login_resp = client.post(
        "/auth/login",
        data={"username": "recepcios_kati", "password": "rec123"},
        follow_redirects=True,
    )
    print("Login status:", login_resp.status_code)

    # Find a booking to act on
    booking = Booking.query.order_by(Booking.id.asc()).first()
    if not booking:
        print("No booking found to test.")
    else:
        print("Testing booking id:", booking.id, "status before:", booking.status)
        action_resp = client.post(
            f"/reception/booking/{booking.id}/action",
            data={"booking_id": booking.id, "action": "check_in"},
            follow_redirects=True,
        )
        print("Action status:", action_resp.status_code)

        # Refresh booking
        b = Booking.query.get(booking.id)
        print("Status after:", b.status)

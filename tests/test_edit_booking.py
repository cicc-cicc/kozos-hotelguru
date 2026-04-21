from datetime import timedelta
import re

from WebApp import create_app
from WebApp.models import User, Booking


def test_edit_booking_flow():
    app = create_app()
    app.config["TESTING"] = True

    with app.app_context():
        user = User.query.filter_by(username="test_robot").first()
        assert user is not None, "Run test_booking first to create test data"

        booking = (
            Booking.query.filter_by(user_id=user.id)
            .order_by(Booking.created_at.desc())
            .first()
        )
        assert (
            booking is not None
        ), "No booking found for test_robot; run tests in order or create booking first"

        client = app.test_client()

        with client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess["_fresh"] = True

        get_resp = client.get(f"/booking/{booking.id}/edit")
        assert get_resp.status_code == 200
        html = get_resp.get_data(as_text=True)

        m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
        csrf = m.group(1) if m else None

        new_arrival = (booking.check_in.date() + timedelta(days=1)).strftime("%Y-%m-%d")
        new_departure = (booking.check_out.date() + timedelta(days=2)).strftime(
            "%Y-%m-%d"
        )

        data = {
            "arrival_date": new_arrival,
            "departure_date": new_departure,
            "guests": "1",
            "csrf_token": csrf,
        }

        resp = client.post(
            f"/booking/{booking.id}/edit", data=data, follow_redirects=True
        )
        assert resp.status_code == 200
        text = resp.get_data(as_text=True)
        assert "sikeresen" in text.lower() or "frissítve" in text

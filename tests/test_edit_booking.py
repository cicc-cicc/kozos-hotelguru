from datetime import timedelta
import re

from WebApp import create_app
from WebApp import db
from WebApp.models import User, Booking, Room
from datetime import datetime


def test_edit_booking_flow():
    app = create_app()
    app.config["TESTING"] = True

    with app.app_context():
        # Ensure tables exist
        db.create_all()

        # Create or get test user
        user = User.query.filter_by(username="test_robot").first()
        if not user:
            user = User(username="test_robot", email="test_robot@example.com", password_hash="x")
            db.session.add(user)
            db.session.commit()

        # Ensure there's at least one room
        room = Room.query.filter_by(room_number="T100").first()
        if not room:
            room = Room(room_number="T100", capacity=2, price_per_night=5000.0, description="Test room")
            db.session.add(room)
            db.session.commit()

        # Create a booking if none exists for the user
        booking = (
            Booking.query.filter_by(user_id=user.id)
            .order_by(Booking.created_at.desc())
            .first()
        )
        if not booking:
            arrival = datetime.utcnow().date()
            departure = arrival + timedelta(days=1)
            booking = Booking(user_id=user.id, room_id=room.id, check_in=datetime.combine(arrival, datetime.min.time()), check_out=datetime.combine(departure, datetime.min.time()), guests=1)
            db.session.add(booking)
            db.session.commit()

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

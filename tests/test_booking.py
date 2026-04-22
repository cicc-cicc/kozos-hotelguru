from datetime import datetime, timedelta
import re

from WebApp import create_app, db
from WebApp.models import User, Room, Booking


def test_booking_flow():
    app = create_app()
    app.config["TESTING"] = True

    with app.app_context():
        # Ensure a clean schema for the test run
        db.drop_all()
        db.create_all()

        # ensure test user
        user = User.query.filter_by(username="test_robot").first()
        if not user:
            user = User(
                username="test_robot", email="test_robot@example.com", password_hash="x"
            )
            db.session.add(user)
            db.session.commit()

        # ensure test room
        room = Room.query.filter_by(room_number="T100").first()
        if not room:
            room = Room(
                room_number="T100",
                capacity=2,
                price_per_night=5000.0,
                description="Test room",
            )
            db.session.add(room)
            db.session.commit()

        arrival = datetime.utcnow().date()
        departure = arrival + timedelta(days=1)

        client = app.test_client()

        # Ensure no conflicting bookings exist for the test room
        bookings_to_remove = Booking.query.filter_by(room_id=room.id).all()
        for b in bookings_to_remove:
            db.session.delete(b)
        db.session.commit()

        # Simulate login by setting session values
        with client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess["_fresh"] = True

        params = {
            "arrival": arrival.strftime("%Y-%m-%d"),
            "departure": departure.strftime("%Y-%m-%d"),
            "guests": "2",
        }
        get_resp = client.get("/search-results", query_string=params)
        assert get_resp.status_code == 200
        html = get_resp.get_data(as_text=True)

        m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
        csrf = m.group(1) if m else None

        data = {
            "room_id": str(room.id),
            "arrival_date": arrival.strftime("%Y-%m-%d"),
            "departure_date": departure.strftime("%Y-%m-%d"),
            "guests": "2",
            "csrf_token": csrf,
        }

        resp = client.post("/book-room", data=data, follow_redirects=True)
        text = resp.get_data(as_text=True)
        assert resp.status_code == 200
        assert "Sikeres foglalás" in text or "Sikeres foglalás" in text

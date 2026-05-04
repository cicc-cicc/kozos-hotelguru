import re
from datetime import datetime, timedelta

from WebApp import db
from WebApp.models import Room, User


def test_booking_script_flow(app, client):
    with app.app_context():
        # Létrehozzuk a teszt felhasználót a tiszta adatbázisban
        user = User.query.filter_by(username="test_robot").first()
        if not user:
            user = User(
                username="test_robot", email="test_robot@example.com", password_hash="x"
            )
            db.session.add(user)

        # Létrehozzuk a teszt szobát
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

        # Foglalási adatok előkészítése
        arrival = datetime.utcnow().date()
        departure = arrival + timedelta(days=1)

        # Bejelentkezés a munkamenet (session) manipulálásával
        with client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess["_fresh"] = True

        # Lekérjük a keresési oldalt a CSRF tokenért
        params = {
            "arrival": arrival.strftime("%Y-%m-%d"),
            "departure": departure.strftime("%Y-%m-%d"),
            "guests": "2",
        }
        get_resp = client.get("/search-results", query_string=params)
        html = get_resp.get_data(as_text=True)

        # Kinyerjük a CSRF tokent
        m = re.search(r'name="csrf_token"\s+type="hidden"\s+value="([^"]+)"', html)
        csrf = m.group(1) if m else None

        data = {
            "room_id": str(room.id),
            "arrival_date": arrival.strftime("%Y-%m-%d"),
            "departure_date": departure.strftime("%Y-%m-%d"),
            "guests": "2",
            "csrf_token": csrf,
            "submit": "Foglalás véglegesítése",
        }

        # Foglalás elküldése
        resp = client.post("/book-room", data=data, follow_redirects=True)

        # Ellenőrizzük az eredményt
        assert resp.status_code in [200, 302], "Hiba történt a foglalás során"

        print("STATUS:", resp.status_code)
        print("LENGTH:", len(resp.data))

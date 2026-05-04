import re
from datetime import datetime, timedelta

from WebApp import db
from WebApp.models import Booking, User, Room


def test_edit_booking_script_flow(app, client):
    with app.app_context():
        # Létrehozzuk a teszt felhasználót, ha még nincs
        user = User.query.filter_by(username="test_robot").first()
        if not user:
            user = User(
                username="test_robot", email="test_robot@example.com", password_hash="x"
            )
            db.session.add(user)
            db.session.commit()

        # Megkeressük a legutóbbi foglalást
        booking = (
            Booking.query.filter_by(user_id=user.id)
            .order_by(Booking.created_at.desc())
            .first()
        )

        # Ha a teszt teljesen üres adatbázisból indul (pl. GitHub), csinálunk neki egy foglalást gyorsan
        if not booking:
            room = Room(room_number="T200", capacity=1, price_per_night=2000.0)
            db.session.add(room)
            db.session.commit()

            arrival = datetime.utcnow()
            booking = Booking(
                user_id=user.id,
                room_id=room.id,
                check_in=arrival,
                check_out=arrival + timedelta(days=2),
                guests_count=1,
            )
            db.session.add(booking)
            db.session.commit()

        assert (
            booking is not None
        ), "Nem sikerült foglalást találni vagy létrehozni a teszthez!"

        # Bejelentkezés
        with client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess["_fresh"] = True

        # Lekérjük a szerkesztő oldalt
        get_resp = client.get(f"/booking/{booking.id}/edit")
        html = get_resp.get_data(as_text=True)

        # Kinyerjük a CSRF tokent
        m = re.search(r'name="csrf_token"\s+type="hidden"\s+value="([^"]+)"', html)
        csrf = m.group(1) if m else None

        # Új dátumok beállítása (+1, +2 nap)
        new_arrival = (booking.check_in.date() + timedelta(days=1)).strftime("%Y-%m-%d")
        new_departure = (booking.check_out.date() + timedelta(days=2)).strftime(
            "%Y-%m-%d"
        )

        data = {
            "arrival_date": new_arrival,
            "departure_date": new_departure,
            "guests": "1",
            "csrf_token": csrf,
            "submit": "Foglalás frissítése",
        }

        # Űrlap elküldése
        resp = client.post(
            f"/booking/{booking.id}/edit", data=data, follow_redirects=True
        )

        assert resp.status_code in [200, 302], "Hiba történt a foglalás szerkesztésekor"

        print("STATUS:", resp.status_code)
        print("LENGTH:", len(resp.data))

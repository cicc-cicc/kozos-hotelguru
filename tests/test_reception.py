from WebApp import db
from WebApp.models import Booking, User, Role
from werkzeug.security import generate_password_hash


# A pytest az (app, client) paramétereket automatikusan betölti nekünk a conftest.py-ból!
def test_reception_booking_action_flow(app, client):
    with app.app_context():
        # Létrehozzuk a recepciós felhasználót a tiszta GitHub Actions db-ben
        if not User.query.filter_by(username="recepcios_kati").first():
            kati = User(
                username="recepcios_kati",
                email="kati@hotel.hu",
                password_hash=generate_password_hash("rec123"),
                role=Role.receptionist,
            )
            db.session.add(kati)
            db.session.commit()

        # Login as receptionist (itt már a fixture-ből kapott 'client'-et használjuk)
        login_resp = client.post(
            "/auth/login",
            data={"username": "recepcios_kati", "password": "rec123"},
            follow_redirects=True,
        )
        assert login_resp.status_code == 200, "Bejelentkezés sikertelen"
        print("Login status:", login_resp.status_code)

        # Find a booking to act on
        booking = Booking.query.order_by(Booking.id.asc()).first()
        assert booking is not None, "No booking found to test."

        print("Testing booking id:", booking.id, "status before:", booking.status)

        # Mivel a CSRF ki lett kapcsolva a conftest.py-ban, ez az akció is simán le fog futni
        action_resp = client.post(
            f"/reception/booking/{booking.id}/action",
            data={"booking_id": booking.id, "action": "check_in"},
            follow_redirects=True,
        )
        assert action_resp.status_code in [200, 302], "Hiba az akció során"
        print("Action status:", action_resp.status_code)

        # JAVÍTÁS: Eltüntettük a sárga figyelmeztetést!
        # A régi Booking.query.get(id) helyett az új db.session.get() metódust használjuk:
        b = db.session.get(Booking, booking.id)
        print("Status after:", b.status)

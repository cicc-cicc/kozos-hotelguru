from WebApp import create_app, db
from WebApp.models import Booking, User, Role
from werkzeug.security import generate_password_hash


def test_reception_booking_action_flow():
    app = create_app()

    # Kifejezetten teszt módba rakjuk az appot, ami kikapcsolja a CSRF védelmet a POST kéréseknél
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        # ÚJ SOR: Létrehozzuk a táblákat
        db.create_all()
        
        # ÚJ BLOKK: Létrehozzuk a recepciós felhasználót a tiszta GitHub Actions db-ben
        if not User.query.filter_by(username="recepcios_kati").first():
            kati = User(
                username="recepcios_kati",
                email="kati@hotel.hu",
                password_hash=generate_password_hash("rec123"),
                role=Role.receptionist
            )
            db.session.add(kati)
            db.session.commit()

        # Use test client to login and perform action
        client = app.test_client()

        # Login as receptionist
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

        # Mivel a CSRF ki lett kapcsolva, ez az akció is simán le fog futni
        action_resp = client.post(
            f"/reception/booking/{booking.id}/action",
            data={"booking_id": booking.id, "action": "check_in"},
            follow_redirects=True,
        )
        assert action_resp.status_code in [200, 302], "Hiba az akció során"
        print("Action status:", action_resp.status_code)

        # Refresh booking
        b = Booking.query.get(booking.id)
        print("Status after:", b.status)
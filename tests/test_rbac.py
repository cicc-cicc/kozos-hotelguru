from WebApp import db
from WebApp.models import User, Role
from werkzeug.security import generate_password_hash


def test_rbac_flow(app, client):
    with app.app_context():
        # 1. LÉPÉS: Felhasználók létrehozása a tiszta teszt adatbázisban

        # Recepciós létrehozása
        if not User.query.filter_by(username="recepcios_kati").first():
            kati = User(
                username="recepcios_kati",
                email="kati@hotel.hu",
                password_hash=generate_password_hash("rec123"),
                role=Role.receptionist,
            )
            db.session.add(kati)

        # Admin létrehozása
        if not User.query.filter_by(username="admin_janos").first():
            janos = User(
                username="admin_janos",
                email="admin@hotel.hu",
                password_hash=generate_password_hash("admin123"),
                role=Role.admin,
            )
            db.session.add(janos)

        db.session.commit()

        # 2. LÉPÉS: Recepciós bejelentkezés és jogosultság tesztelése

        resp = client.post(
            "/auth/login",
            data={"username": "recepcios_kati", "password": "rec123"},
            follow_redirects=True,
        )
        assert resp.status_code == 200, "Recepciós bejelentkezés sikertelen"
        print("Recep login status", resp.status_code)

        # Try admin page
        r = client.get("/admin/dashboard")
        print("/admin/dashboard status for receptionist:", r.status_code)
        # Egy recepciós nem láthatja az admin felületet (403 Forbidden vagy 302 Redirect kell legyen)
        assert r.status_code in [
            403,
            302,
        ], f"Hiba: A recepciós láthatja az admint! Státusz: {r.status_code}"

        # 3. LÉPÉS: Admin bejelentkezés és jogosultság tesztelése

        # Logout
        client.get("/auth/logout")

        # Admin login
        resp2 = client.post(
            "/auth/login",
            data={"username": "admin_janos", "password": "admin123"},
            follow_redirects=True,
        )
        assert resp2.status_code == 200, "Admin bejelentkezés sikertelen"
        print("Admin login status", resp2.status_code)

        # Try admin page again
        r2 = client.get("/admin/dashboard")
        print("/admin/dashboard status for admin:", r2.status_code)
        # Az admin viszont sikeresen be kell tudjon lépni (200 OK)
        assert (
            r2.status_code == 200
        ), f"Hiba: Az admin nem éri el az admin felületet! Státusz: {r2.status_code}"

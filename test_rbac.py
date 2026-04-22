from WebApp import create_app

app = create_app()

with app.app_context():
    # Disable CSRF for test client interactions
    app.config["WTF_CSRF_ENABLED"] = False
    client = app.test_client()

    # Login as receptionist
    resp = client.post(
        "/auth/login",
        data={"username": "recepcios_kati", "password": "rec123"},
        follow_redirects=True,
    )
    print("Recep login status", resp.status_code)
    # Try admin page
    r = client.get("/admin/dashboard")
    print("/admin/dashboard status for receptionist:", r.status_code)

    # Logout and login as admin
    client.get("/auth/logout")
    resp2 = client.post(
        "/auth/login",
        data={"username": "admin_janos", "password": "admin123"},
        follow_redirects=True,
    )
    print("Admin login status", resp2.status_code)
    r2 = client.get("/admin/dashboard")
    print("/admin/dashboard status for admin:", r2.status_code)

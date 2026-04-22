import sys
import os


def main() -> None:
    # ensure project root is on sys.path when script is executed from scripts/
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)

    from WebApp import create_app
    from WebApp.models import User
    from werkzeug.security import check_password_hash

    app = create_app()
    with app.app_context():
        u = User.query.filter_by(username="admin_janos").first()
        if not u:
            print("ADMIN USER NOT FOUND")
        else:
            print("FOUND:", u.username, u.email, "role=", u.role.name)
            print("password_hash present:", bool(u.password_hash))
            # test provided password
            print(
                "check admin123:",
                check_password_hash(u.password_hash or "", "admin123"),
            )
            print("raw hash:", u.password_hash)


if __name__ == "__main__":
    main()

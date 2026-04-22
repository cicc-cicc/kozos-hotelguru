import sys
import os
import json


def main() -> None:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)

    from WebApp import create_app
    from WebApp.models import User

    app = create_app()
    with app.app_context():
        users = User.query.order_by(User.id).all()
        print(f"Users in DB ({len(users)}):")
        for u in users:
            print(
                f"- id={u.id} username={u.username} email={u.email} role={u.role.name} created={u.created_at}"
            )

        # Compare to data.json
        data_path = os.path.join(PROJECT_ROOT, "data.json")
        if os.path.exists(data_path):
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            json_users = [u["username"] for u in data.get("users", [])]
            missing = [
                name for name in json_users if not any(u.username == name for u in users)
            ]
            extra = [u.username for u in users if u.username not in json_users]
            print("\nUsers in data.json:", json_users)
            print("Missing from DB (present in data.json but not DB):", missing)
            print("Extra in DB (not in data.json):", extra)
        else:
            print("\nNo data.json found to compare.")


if __name__ == "__main__":
    main()

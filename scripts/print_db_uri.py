import sys
import os


def main() -> None:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)

    from WebApp import create_app

    app = create_app()
    with app.app_context():
        print("SQLALCHEMY_DATABASE_URI =", app.config.get("SQLALCHEMY_DATABASE_URI"))


if __name__ == "__main__":
    main()

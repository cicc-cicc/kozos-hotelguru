from WebApp import create_app
app = create_app()


def _print_startup_info(app):
    try:
        with app.app_context():
            db_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
            print(f"Resolved SQLALCHEMY_DATABASE_URI: {db_uri}")
            # show a few quick counts so it's obvious which DB we're using
            try:
                from WebApp.models import User, Room, Booking

                print("Users:", User.query.count())
                print("Rooms:", Room.query.count())
                print("Bookings:", Booking.query.count())
            except Exception:
                pass
    except Exception:
        pass


if __name__ == "__main__":
    _print_startup_info(app)
    # Disable the reloader to avoid double-process surprises during startup.
    app.run(host="localhost", port=5555, debug=True, use_reloader=False)

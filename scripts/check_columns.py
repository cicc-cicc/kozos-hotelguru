import os
import sys

print("CWD:", os.getcwd())
print("PYTHONPATH first entries:", sys.path[:3])
# Ensure project root is on sys.path so 'WebApp' package can be imported
proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)
    print("Inserted project root into sys.path:", proj_root)
try:
    from WebApp import create_app, db
    from sqlalchemy import inspect
    import json

    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        cols = [c["name"] for c in inspector.get_columns("rooms")]
        print(json.dumps(cols))
        # Run a simple query to verify ORM access
        try:
            from WebApp.models import Room

            rooms = Room.query.filter(Room.capacity >= 2).limit(5).all()
            print("Sample rooms fetched:", len(rooms))
        except Exception as e:
            print("ERROR running sample query:", e)
except Exception as e:
    print("ERROR IMPORTING APP:", e)

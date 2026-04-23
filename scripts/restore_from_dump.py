import os
import sys
import gzip
import json
from datetime import datetime

# ensure project root
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from WebApp import create_app, db
from WebApp.models import (
    User,
    Room,
    Booking,
    ExtraService,
    BookingStatus,
)

app = create_app()

BACKUP_DIR = os.path.join(ROOT, "backups")


def find_latest_dump():
    dumps = [
        f
        for f in os.listdir(BACKUP_DIR)
        if f.startswith("db-dump-") and f.endswith(".json.gz")
    ]
    if not dumps:
        return None
    dumps.sort()
    return os.path.join(BACKUP_DIR, dumps[-1])


def parse_dt(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        try:
            return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None


def upsert_from_dump(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        data = json.load(f)

    with app.app_context():
        # Users
        for u in data.get("users", []):
            existing = User.query.filter_by(username=u.get("username")).first()
            if existing:
                continue
            new = User(
                username=u.get("username"),
                email=u.get("email") or f"{u.get('username')}@example.local",
                password_hash=None,
                phone=u.get("phone"),
                address=u.get("address"),
            )
            # Role handling
            try:
                from WebApp.models import Role

                new.role = Role[u.get("role")]
            except Exception:
                pass
            db.session.add(new)
        db.session.flush()

        # Extra services
        svc_map = {}
        for s in data.get("extraservices", []):
            existing = ExtraService.query.filter_by(name=s.get("name")).first()
            if existing:
                svc_map[existing.name] = existing
                continue
            svc = ExtraService(
                name=s.get("name"),
                price=s.get("price") or 0.0,
                description=s.get("description"),
            )
            db.session.add(svc)
            db.session.flush()
            svc_map[svc.name] = svc

        # Rooms
        room_map = {}
        for r in data.get("rooms", []):
            existing = Room.query.filter_by(room_number=r.get("room_number")).first()
            if existing:
                room_map[existing.room_number] = existing
                continue
            room = Room(
                room_number=r.get("room_number"),
                capacity=r.get("capacity") or 1,
                price_per_night=r.get("price_per_night") or 0.0,
                description=r.get("description"),
            )
            db.session.add(room)
            db.session.flush()
            room_map[room.room_number] = room

        db.session.flush()

        # Bookings
        for b in data.get("bookings", []):
            # avoid duplicates using a heuristic: user+room+check_in
            user = User.query.filter_by(username=b.get("username")).first()
            room = Room.query.filter_by(room_number=b.get("room_number")).first()
            if not user or not room:
                continue
            check_in = parse_dt(b.get("check_in"))
            check_out = parse_dt(b.get("check_out"))
            exists = Booking.query.filter_by(
                user_id=user.id, room_id=room.id, check_in=check_in
            ).first()
            if exists:
                continue
            status = b.get("status")
            try:
                status_enum = BookingStatus[status]
            except Exception:
                status_enum = BookingStatus.pending
            booking = Booking(
                user_id=user.id,
                room_id=room.id,
                check_in=check_in,
                check_out=check_out,
                status=status_enum,
                total_price=b.get("total_price"),
            )
            db.session.add(booking)
            db.session.flush()

            # booking services and invoice handled if present in dump items listings
        try:
            db.session.commit()
            print("Restore committed successfully")
        except Exception as e:
            db.session.rollback()
            print("Restore failed:", e)


if __name__ == "__main__":
    dump = find_latest_dump()
    if not dump:
        print("No dump files found in", BACKUP_DIR)
        sys.exit(1)
    print("Restoring from", dump)
    upsert_from_dump(dump)
    print("Done")

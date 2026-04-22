import os
import sys
import json
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from WebApp import create_app, db
from WebApp.models import (
    User,
    Room,
    Booking,
    ExtraService,
    BookingService,
    Invoice,
    Role,
    RoomStatus,
    BookingStatus,
)
from werkzeug.security import generate_password_hash


def parse_dt(value):
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None


def upsert_from_json(app, json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    with app.app_context():
        # Users
        for u in data.get("users", []):
            username = u.get("username")
            if not username:
                continue
            exists = User.query.filter_by(username=username).first()
            if exists:
                # update basic fields
                exists.email = u.get("email") or exists.email
                exists.phone = u.get("phone") or exists.phone
                exists.address = u.get("address") or exists.address
                try:
                    exists.role = Role[u.get("role")]
                except Exception:
                    pass
                db.session.add(exists)
                continue

            pwd = u.get("password") or ""
            password_hash = generate_password_hash(pwd) if pwd else None
            role_value = u.get("role", "guest")
            try:
                role_enum = Role[role_value]
            except Exception:
                role_enum = Role.guest

            new_user = User(
                username=username,
                email=u.get("email") or f"{username}@example.local",
                password_hash=password_hash,
                phone=u.get("phone"),
                address=u.get("address"),
                role=role_enum,
            )
            db.session.add(new_user)

        db.session.flush()

        # Extra services
        services_map = {}
        for s in data.get("extraservices", []):
            name = s.get("name")
            if not name:
                continue
            svc = ExtraService.query.filter_by(name=name).first()
            if svc:
                services_map[svc.name] = svc
                continue
            svc = ExtraService(name=name, description=s.get("description"), price=s.get("price", 0.0))
            db.session.add(svc)
            db.session.flush()
            services_map[svc.name] = svc

        # Rooms
        rooms_map = {}
        for r in data.get("rooms", []):
            num = r.get("room_number")
            if not num:
                continue
            existing = Room.query.filter_by(room_number=num).first()
            status_value = r.get("status", "available")
            try:
                status_enum = RoomStatus[status_value]
            except Exception:
                status_enum = RoomStatus.available

            if existing:
                existing.capacity = r.get("capacity", existing.capacity)
                existing.price_per_night = r.get("price_per_night", existing.price_per_night)
                existing.description = r.get("description", existing.description)
                existing.status = status_enum
                db.session.add(existing)
                rooms_map[existing.room_number] = existing
                continue

            room = Room(
                room_number=num,
                capacity=r.get("capacity", 1),
                price_per_night=r.get("price_per_night", 0.0),
                description=r.get("description"),
                status=status_enum,
            )
            db.session.add(room)
            db.session.flush()
            rooms_map[room.room_number] = room

        db.session.flush()

        # Bookings
        for b in data.get("bookings", []):
            username = b.get("username")
            room_number = b.get("room_number")
            user = User.query.filter_by(username=username).first()
            room = Room.query.filter_by(room_number=room_number).first()
            if not user or not room:
                continue
            check_in = parse_dt(b.get("check_in"))
            check_out = parse_dt(b.get("check_out"))
            if not check_in or not check_out:
                continue

            exists = Booking.query.filter_by(user_id=user.id, room_id=room.id, check_in=check_in).first()
            if exists:
                continue

            status_val = b.get("status", "pending")
            try:
                status_enum = BookingStatus[status_val]
            except Exception:
                status_enum = BookingStatus.pending

            booking = Booking(
                user_id=user.id,
                room_id=room.id,
                check_in=check_in,
                check_out=check_out,
                status=status_enum,
            )
            db.session.add(booking)
            db.session.flush()

            extras = b.get("extra_services", [])
            for ex in extras:
                svc = services_map.get(ex.get("service_name"))
                if not svc:
                    continue
                qty = int(ex.get("quantity", 1))
                bs = BookingService(booking_id=booking.id, service_id=svc.id, quantity=qty)
                db.session.add(bs)

            inv_data = b.get("invoice")
            if inv_data:
                invoice = Invoice(booking_id=booking.id, total_amount=inv_data.get("total_amount") or 0.0, paid=bool(inv_data.get("paid", False)))
                db.session.add(invoice)

        try:
            db.session.commit()
            print("Upsert from data.json completed successfully")
        except Exception as e:
            db.session.rollback()
            print("Error during upsert:", e)


if __name__ == "__main__":
    app = create_app()
    json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data.json")
    if not os.path.exists(json_path):
        print("data.json not found at", json_path)
        sys.exit(1)
    upsert_from_json(app, json_path)

import os
import sys
import json
from datetime import datetime
import gzip

# Ensure project root is on sys.path when run from scripts/
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from WebApp import create_app
from WebApp.models import User, Room, Booking, ExtraService, BookingService, Invoice

app = create_app()

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def serialize(obj):
    if obj is None:
        return None
    if isinstance(obj, datetime):
        return obj.isoformat()
    try:
        # Enum values
        return obj.value
    except Exception:
        pass
    return str(obj)


with app.app_context():
    data = {}
    data["users"] = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "phone": u.phone,
            "address": u.address,
            "role": getattr(u.role, "value", str(u.role)),
            "created_at": serialize(u.created_at),
        }
        for u in User.query.all()
    ]

    data["rooms"] = [
        {
            "id": r.id,
            "room_number": r.room_number,
            "capacity": r.capacity,
            "price_per_night": r.price_per_night,
            "description": r.description,
            "status": getattr(r.status, "value", str(r.status)),
        }
        for r in Room.query.all()
    ]

    data["extraservices"] = [
        {"id": s.id, "name": s.name, "price": s.price, "description": s.description}
        for s in ExtraService.query.all()
    ]

    data["bookings"] = [
        {
            "id": b.id,
            "user_id": b.user_id,
            "room_id": b.room_id,
            "check_in": serialize(b.check_in),
            "check_out": serialize(b.check_out),
            "status": getattr(b.status, "value", str(b.status)),
            "created_at": serialize(b.created_at),
            "total_price": b.total_price,
        }
        for b in Booking.query.all()
    ]

    data["booking_services"] = [
        {
            "id": bs.id,
            "booking_id": bs.booking_id,
            "service_id": bs.service_id,
            "quantity": bs.quantity,
        }
        for bs in BookingService.query.all()
    ]

    data["invoices"] = [
        {
            "id": inv.id,
            "booking_id": inv.booking_id,
            "total_amount": inv.total_amount,
            "paid": inv.paid,
            "created_at": serialize(inv.created_at),
        }
        for inv in Invoice.query.all()
    ]

    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_path = os.path.join(OUTPUT_DIR, f"db-dump-{ts}.json.gz")
    with gzip.open(out_path, "wt", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("DB dumped to", out_path)

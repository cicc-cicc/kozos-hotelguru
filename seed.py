import json
import os
from datetime import datetime

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

app = create_app()


def parse_dt(value):
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def seed_database():
    with app.app_context():
        # Foglalások törlése, hogy ne legyenek idegen kulcs hibák
        from WebApp.models import Booking, BookingService, Invoice, ExtraService
        Invoice.query.delete()
        db.session.commit()
        BookingService.query.delete()
        db.session.commit()
        Booking.query.delete()
        db.session.commit()
        Room.query.delete()
        db.session.commit()
        ExtraService.query.delete()
        db.session.commit()
        print("Invoice, BookingService, Booking, Room és ExtraService tábla kiürítve.")

        # Fejlesztői fallback: ha nincsenek migrációk lefuttatva, biztosítjuk, hogy a táblák létrejöjjenek.
        # Ez helyben gyorsan segít elkerülni a "Table doesn't exist" hibát. Production környezetben
        # érdemes migrációkat használni és ezt a sort eltávolítani.
        db.create_all()
        print("db.create_all() futtatva — a táblák biztosítva.")

        json_path = os.path.join(os.path.dirname(__file__), "data.json")

        if not os.path.exists(json_path):
            print(f"Hiba: Nem találom a fájlt itt: {json_path}")
            return

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        print("Adatok betöltése folyamatban...")

        # 1) Felhasználók
        for u in data.get("users", []):
            exists = User.query.filter_by(username=u["username"]).first()
            if exists:
                print(f"Felhasználó már létezik: {u['username']}")
                continue

            pwd = u.get("password") or ""
            password_hash = generate_password_hash(pwd) if pwd else None
            role_value = u.get("role", "guest")
            try:
                role_enum = Role[role_value]
            except Exception:
                role_enum = Role.guest

            new_user = User(
                username=u["username"],
                email=u.get("email"),
                password_hash=password_hash,
                phone=u.get("phone"),
                address=u.get("address"),
                role=role_enum,
            )
            db.session.add(new_user)
            print(f"Felhasználó hozzáadva: {u['username']}")

        db.session.flush()

        # 2) Szolgáltatások
        services_map = {}
        for s in data.get("extraservices", []):
            svc = ExtraService.query.filter_by(name=s["name"]).first()
            if svc:
                services_map[svc.name] = svc
                continue
            svc = ExtraService(name=s["name"], description=s.get("description"), price=s.get("price", 0.0))
            db.session.add(svc)
            db.session.flush()
            services_map[svc.name] = svc
            print(f"ExtraService hozzáadva: {svc.name}")

        # 3) Szobák
        rooms_map = {}
        for r in data.get("rooms", []):
            existing = Room.query.filter_by(room_number=r["room_number"]).first()
            status_value = r.get("status", "available")
            try:
                status_enum = RoomStatus[status_value]
            except Exception:
                status_enum = RoomStatus.available

            if existing:
                # Frissítjük a meglévő szoba adatait
                existing.capacity = r.get("capacity", existing.capacity)
                existing.price_per_night = r.get("price_per_night", existing.price_per_night)
                existing.description = r.get("description", existing.description)
                existing.status = status_enum
                db.session.add(existing)
                rooms_map[existing.room_number] = existing
                print(f"Szoba frissítve: {existing.room_number}")
            else:
                room = Room(
                    room_number=r["room_number"],
                    capacity=r.get("capacity", 1),
                    price_per_night=r.get("price_per_night", 0.0),
                    description=r.get("description"),
                    status=status_enum,
                )
                db.session.add(room)
                db.session.flush()
                rooms_map[room.room_number] = room
                print(f"Szoba hozzáadva: {room.room_number}")

        db.session.flush()

        # 4) Foglalások
        for b in data.get("bookings", []):
            user = User.query.filter_by(username=b["username"]).first()
            room = Room.query.filter_by(room_number=b["room_number"]).first()
            if not user or not room:
                print(f"Hiányzó user vagy room a foglaláshoz: {b}")
                continue

            check_in = parse_dt(b.get("check_in"))
            check_out = parse_dt(b.get("check_out"))
            if not check_in or not check_out:
                print(f"Érvénytelen dátum a foglalásban: {b}")
                continue

            # Ütközés ellenőrzés
            if Booking.has_conflict(room.id, check_in, check_out):
                print(f"Ütköző foglalás, kihagyva: user={user.username} room={room.room_number} {check_in}->{check_out}")
                continue

            # státusz
            status_val = b.get("status", "pending")
            try:
                status_enum = BookingStatus[status_val]
            except Exception:
                status_enum = BookingStatus.pending

            # számoljuk az árat: éjszakák * ár + extra szolgáltatások
            nights = max(1, (check_out.date() - check_in.date()).days)
            base_price = nights * (room.price_per_night or 0.0)

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
            extras_total = 0.0
            for ex in extras:
                svc = services_map.get(ex.get("service_name"))
                if not svc:
                    print(f"Ismeretlen szolgáltatás: {ex.get('service_name')}")
                    continue
                qty = int(ex.get("quantity", 1))
                bs = BookingService(booking_id=booking.id, service_id=svc.id, quantity=qty)
                db.session.add(bs)
                extras_total += (svc.price or 0.0) * qty

            total_price = b.get("invoice", {}).get("total_amount")
            if total_price is None:
                total_price = base_price + extras_total

            booking.total_price = total_price

            inv_data = b.get("invoice")
            if inv_data:
                invoice = Invoice(booking_id=booking.id, total_amount=total_price, paid=bool(inv_data.get("paid", False)))
                db.session.add(invoice)

            print(f"Foglalás létrehozva: user={user.username} room={room.room_number} {check_in}->{check_out}")

        # végső mentés
        try:
            db.session.commit()
            print("\nSikeres feltöltés! Az adatbázis készen áll a használatra.")
        except Exception as e:
            db.session.rollback()
            print(f"\nHiba történt a mentés során: {e}")


if __name__ == "__main__":
    seed_database()
from datetime import datetime
from ..models import Room, Booking, Invoice, BookingStatus
from .. import db


def create_booking(
    user_id, room_id, check_in, check_out, guests_count=1, price_per_person=False
):
    """Létrehoz egy foglalást és a hozzá tartozó számlát.

    Dob ValueError-t, ha a szoba nem elérhető vagy más üzleti hiba van.
    Visszatérési érték: (booking, invoice)
    """
    room = Room.query.get_or_404(int(room_id))

    # Ellenőrzés az üzleti logika szerint
    if not room.is_available_for(check_in, check_out):
        raise ValueError("A kiválasztott szoba nem elérhető a megadott időpontra.")

    total_price = calculate_total_price(
        room,
        check_in,
        check_out,
        guests_count=guests_count,
        price_per_person=price_per_person,
    )

    booking = Booking(
        user_id=user_id,
        room_id=room.id,
        check_in=check_in,
        check_out=check_out,
        status=BookingStatus.pending,
        total_price=total_price,
        guests_count=guests_count,
    )

    db.session.add(booking)
    db.session.flush()  # hogy legyen booking.id

    invoice = Invoice(booking_id=booking.id, total_amount=total_price, paid=False)
    db.session.add(invoice)

    db.session.commit()

    return booking, invoice


def calculate_total_price(
    room: Room,
    check_in,
    check_out,
    guests_count: int = 1,
    price_per_person: bool = False,
    extras: float = 0.0,
):
    """Központi árkalkulátor: kiszámolja az alapárat (éjszakák * price_per_night),
    és opcionálisan figyelembe veszi a főre jutó árazást és az extra szolgáltatásokat.
    Visszaad egy lebegőpontos értéket.
    """
    nights = max(1, (check_out - check_in).days)
    if price_per_person:
        base = nights * (room.price_per_night or 0.0) * (guests_count or 1)
    else:
        base = nights * (room.price_per_night or 0.0)

    return base + (extras or 0.0)

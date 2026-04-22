from datetime import datetime

from flask_login import current_user

from .. import db
from ..models import (
    Booking,
    BookingStatus,
    BookingService,
    ExtraService,
    RoomStatus,
    AuditLog,
)


def perform_booking_action(booking: Booking, action: str):
    if action == "confirm":
        booking.confirm()
        # Audit
        try:
            user_id = getattr(current_user, "id", None)
            db.session.add(
                AuditLog(
                    user_id=user_id,
                    booking_id=booking.id,
                    action="confirm",
                    details=f"Confirmed booking {booking.id} by user {user_id}",
                    created_at=datetime.utcnow(),
                )
            )
        except Exception:
            pass
    elif action == "check_in":
        booking.check_in_action()
        # Mark room occupied when guest checks in
        try:
            room = booking.room
            if room:
                room.status = RoomStatus.occupied
                db.session.add(room)
        except Exception:
            pass
        # Audit
        try:
            user_id = getattr(current_user, "id", None)
            db.session.add(
                AuditLog(
                    user_id=user_id,
                    booking_id=booking.id,
                    action="check_in",
                    details=f"Checked in booking {booking.id} by user {user_id}",
                    created_at=datetime.utcnow(),
                )
            )
        except Exception:
            pass
    elif action == "check_out":
        booking.check_out_action()
        # Mark invoice paid and room available
        if booking.invoice:
            booking.invoice.paid = True
        try:
            room = booking.room
            if room:
                room.status = RoomStatus.available
                db.session.add(room)
        except Exception:
            pass
        # Audit
        try:
            user_id = getattr(current_user, "id", None)
            db.session.add(
                AuditLog(
                    user_id=user_id,
                    booking_id=booking.id,
                    action="check_out",
                    details=f"Checked out booking {booking.id} by user {user_id}",
                    created_at=datetime.utcnow(),
                )
            )
        except Exception:
            pass
    elif action == "cancel":
        booking.cancel()
        # Audit
        try:
            user_id = getattr(current_user, "id", None)
            db.session.add(
                AuditLog(
                    user_id=user_id,
                    booking_id=booking.id,
                    action="cancel",
                    details=f"Cancelled booking {booking.id} by user {user_id}",
                    created_at=datetime.utcnow(),
                )
            )
        except Exception:
            pass
    else:
        raise ValueError("Ismeretlen művelet.")

    db.session.commit()


def add_extra_service_to_booking(booking: Booking, service_id: int, quantity: int):
    svc = ExtraService.query.get_or_404(service_id)
    if booking.status in [BookingStatus.cancelled, BookingStatus.checked_out]:
        raise ValueError("Lezárt vagy lemondott foglaláshoz nem adható szolgáltatás.")

    new_service = BookingService(
        booking_id=booking.id, service_id=svc.id, quantity=quantity
    )
    db.session.add(new_service)

    extra_cost = svc.price * quantity
    booking.total_price = (booking.total_price or 0) + extra_cost
    if booking.invoice:
        booking.invoice.total_amount = (booking.invoice.total_amount or 0) + extra_cost

    db.session.commit()
    return new_service

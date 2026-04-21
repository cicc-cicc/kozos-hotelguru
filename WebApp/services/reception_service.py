from .. import db
from ..models import Booking, BookingStatus, BookingService, ExtraService


def perform_booking_action(booking: Booking, action: str):
    if action == "confirm":
        booking.confirm()
    elif action == "check_in":
        booking.check_in_action()
    elif action == "check_out":
        booking.check_out_action()
        if booking.invoice:
            booking.invoice.paid = True
    elif action == "cancel":
        booking.cancel()
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

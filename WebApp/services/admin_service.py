from .. import db
from ..models import Room


def create_room_from_form(form):
    existing = Room.query.filter_by(room_number=form.room_number.data).first()
    if existing:
        raise ValueError(f"A {form.room_number.data} szobaszám már foglalt!")

    room = Room(
        room_number=form.room_number.data,
        capacity=form.capacity.data,
        price_per_night=form.price_per_night.data,
        equipment=form.equipment.data,
        description=form.description.data,
    )
    room.set_status(form.status.data)
    db.session.add(room)
    db.session.commit()
    return room


def update_room_from_form(room, form):
    if form.room_number.data != room.room_number:
        existing = Room.query.filter_by(room_number=form.room_number.data).first()
        if existing:
            raise ValueError(f"A {form.room_number.data} szobaszám már létezik!")

    room.room_number = form.room_number.data
    room.capacity = form.capacity.data
    room.price_per_night = form.price_per_night.data
    room.equipment = form.equipment.data
    room.description = form.description.data
    room.set_status(form.status.data)

    db.session.commit()
    return room


def delete_room(room):
    # Prevent accidental removal when there are active bookings
    if room.bookings and len(room.bookings) > 0:
        raise ValueError(
            "A szobához kapcsolódó foglalások vannak. Előbb töröld a foglalásokat."
        )

    deleted_number = room.room_number
    db.session.delete(room)
    db.session.commit()
    return deleted_number

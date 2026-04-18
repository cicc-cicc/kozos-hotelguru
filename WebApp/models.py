from . import db
from datetime import datetime
from flask_login import UserMixin
from enum import Enum, auto, unique

class Role(Enum):
    guest = "guest"
    receptionist = "receptionist"
    manager = "manager"
    admin = "admin"
    
class RoomStatus(Enum):
    available = "available"
    occupied = "occupied"
    maintenance = "maintenance"
    unavailable = "unavailable"

class BookingStatus(Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    checked_in = "checked_in"
    checked_out = "checked_out"

class User(db.Model, UserMixin  ):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    role = db.Column(db.Enum(Role), nullable=False, default=Role.guest)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Kapcsolatok
    bookings = db.relationship("Booking", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} username={self.username} role={self.role.value}>"


class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(10), unique=True, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    price_per_night = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    equipment = db.Column(db.Text, nullable=True)  # Felszereltség, vesszővel elválasztva
    status = db.Column(db.Enum(RoomStatus), nullable=False, default=RoomStatus.available)

    # Kapcsolatok
    bookings = db.relationship("Booking", back_populates="room", cascade="all, delete-orphan")

    @property
    def equipment_list(self):
        if not self.equipment:
            return []
        return [item.strip() for item in self.equipment.split(",") if item.strip()]

    @property
    def is_available(self):
        return self.status == RoomStatus.available
    
    def __repr__(self):
        return f"<Room id={self.id} number={self.room_number} status={self.status.value}>"

    # --- Helper metódusok a frontend gombjaihoz és üzleti logikához ---
    def set_status(self, new_status):
        """Állapot beállítása enum értékkel vagy stringgel.
        Például a frontendről érkező gombok meghívhatják ezt.
        """
        if isinstance(new_status, str):
            try:
                new_status = RoomStatus[new_status]
            except Exception:
                raise ValueError(f"Ismeretlen RoomStatus: {new_status}")
        self.status = new_status

    @property
    def is_available(self):
        """Egyszerű boolean jelzés, hogy a szoba állapota `available`-e."""
        return self.status == RoomStatus.available

    def is_available_for(self, check_in, check_out):
        """Ellenőrzi, hogy a szoba szabad-e a megadott időszakra.
        (Használja a Booking.has_conflict logikát.)
        """
        return not Booking.has_conflict(self.id, check_in, check_out)


# Üzleti szabály (alkalmazási szinten érvényesítve):
# Egy szoba nem rendelkezhet átfedő foglalásokkal. Egy foglalás ütközik, ha:
# existing_booking.check_in < new_check_out ÉS existing_booking.check_out > new_check_in
class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)
    check_in = db.Column(db.DateTime, nullable=False)
    check_out = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Enum(BookingStatus), nullable=False, default=BookingStatus.pending)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total_price = db.Column(db.Float, nullable=True)

    # Kapcsolatok
    user = db.relationship("User", back_populates="bookings")
    room = db.relationship("Room", back_populates="bookings")
    # Asszociációs objektumok az extra szolgáltatásokhoz
    booking_services = db.relationship("BookingService", back_populates="booking", cascade="all, delete-orphan")

    # Kényelmi, csak olvasható kapcsolat az ExtraService objektumokhoz az asszociációs táblán keresztül
    extra_services = db.relationship(
        "ExtraService",
        secondary="booking_services",
        back_populates="bookings",
        viewonly=True,
    )

    # Egy-az-egyhez számla
    invoice = db.relationship("Invoice", back_populates="booking", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return (
            f"<Booking id={self.id} user_id={self.user_id} room_id={self.room_id}"
            f" check_in={self.check_in} check_out={self.check_out} status={self.status.value}>"
        )

    # --- Foglalás állapotkezelő segédfüggvények a frontendhez ---
    def confirm(self):
        """Foglalás megerősítése; ellenőrzi az ütközést és státuszt állít."""
        if Booking.has_conflict(self.room_id, self.check_in, self.check_out, exclude_booking_id=self.id):
            raise ValueError("Ütköző foglalás miatt nem erősíthető meg.")
        self.status = BookingStatus.confirmed

    def cancel(self):
        self.status = BookingStatus.cancelled

    def check_in_action(self):
        self.status = BookingStatus.checked_in

    def check_out_action(self):
        self.status = BookingStatus.checked_out

    @classmethod
    def has_conflict(cls, room_id, new_check_in, new_check_out, exclude_booking_id=None):
        query = cls.query.filter(
            cls.room_id == room_id,
            cls.check_in < new_check_out,
            cls.check_out > new_check_in,
            cls.status != BookingStatus.cancelled,
        )
        if exclude_booking_id:
            query = query.filter(cls.id != exclude_booking_id)
        return query.first() is not None
                    


class BookingService(db.Model):
    __tablename__ = "booking_services"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("extraservices.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    # Kapcsolatok
    booking = db.relationship("Booking", back_populates="booking_services")
    service = db.relationship("ExtraService", back_populates="booking_services")

    def __repr__(self):
        return f"<BookingService id={self.id} booking_id={self.booking_id} service_id={self.service_id} qty={self.quantity}>"

class ExtraService(db.Model):
    __tablename__ = "extraservices"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Kapcsolatok
    booking_services = db.relationship("BookingService", back_populates="service", cascade="all, delete-orphan")
    bookings = db.relationship(
        "Booking",
        secondary="booking_services",
        back_populates="extra_services",
        viewonly=True,
    )

    def __repr__(self):
        return f"<ExtraService id={self.id} name={self.name} price={self.price}>"

class Invoice(db.Model):
    __tablename__ = "invoices"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), unique=True, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    paid = db.Column(db.Boolean, nullable=False, default=False)

    # Egy-az-egyhez kapcsolat vissza a foglaláshoz
    booking = db.relationship("Booking", back_populates="invoice")

    def __repr__(self):
        return f"<Invoice id={self.id} booking_id={self.booking_id} total={self.total_amount} paid={self.paid}>"


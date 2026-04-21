from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    abort,
    current_app,
)
from flask_login import login_required, current_user
from datetime import datetime

from .. import db
from ..models import Room, Booking, BookingStatus, ExtraService, BookingService
from ..services.booking_service import create_booking
from ..forms.booking_forms import (
    RoomSearchForm,
    BookingRequestForm,
    BookingCancelForm,
    BookingEditForm,
)
from ..forms.service_forms import GuestServiceOrderForm

# Blueprint létrehozása 'guest' néven
guest_bp = Blueprint("guest", __name__)


@guest_bp.route("/", methods=["GET", "POST"])
def index():
    """Főoldal és szobakeresés indítása"""
    form = RoomSearchForm()

    if form.validate_on_submit():
        # A keresési adatokat URL paraméterként átadjuk a találati oldalnak
        return redirect(
            url_for(
                "guest.search_results",
                arrival=form.arrival_date.data.strftime("%Y-%m-%d"),
                departure=form.departure_date.data.strftime("%Y-%m-%d"),
                guests=form.guests.data,
            )
        )

    # Alapértelmezett kezdőképernyő a keresővel
    return render_template("index.html", form=form)


@guest_bp.route("/search-results")
def search_results():
    """Szabad szobák listázása a megadott paraméterek alapján"""
    arrival_str = request.args.get("arrival")
    departure_str = request.args.get("departure")
    guests = request.args.get("guests", type=int)

    if not arrival_str or not departure_str or not guests:
        flash("Érvénytelen keresési paraméterek!", "warning")
        return redirect(url_for("guest.index"))

    check_in = datetime.strptime(arrival_str, "%Y-%m-%d")
    check_out = datetime.strptime(departure_str, "%Y-%m-%d")

    # 1. Lekérjük az összes szobát, amibe befér ennyi ember
    suitable_rooms = Room.query.filter(Room.capacity >= guests).all()

    # 2. Leszűrjük azokat, amik szabadok az adott időszakban
    available_rooms = [
        room for room in suitable_rooms if room.is_available_for(check_in, check_out)
    ]

    # Készítünk egy foglalási formot, amit majd a sablonban használunk
    booking_form = BookingRequestForm()
    booking_form.arrival_date.data = arrival_str
    booking_form.departure_date.data = departure_str
    booking_form.guests.data = str(guests)

    return render_template(
        "search_results.html",
        rooms=available_rooms,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        form=booking_form,
    )


@guest_bp.route("/book-room", methods=["POST"])
@login_required  # Foglalni csak bejelentkezve lehet
def book_room():
    """Foglalás rögzítése és számla (Invoice) generálása"""
    try:
        form = BookingRequestForm()

        if form.validate_on_submit():
            # Form-ból jövő adatokat parse-oljuk
            check_in = datetime.strptime(form.arrival_date.data, "%Y-%m-%d")
            check_out = datetime.strptime(form.departure_date.data, "%Y-%m-%d")
            guests_count = (
                int(form.guests.data)
                if getattr(form, "guests", None) and form.guests.data
                else 1
            )

            try:
                create_booking(
                    user_id=current_user.id,
                    room_id=int(form.room_id.data),
                    check_in=check_in,
                    check_out=check_out,
                    guests_count=guests_count,
                    price_per_person=current_app.config.get("PRICE_PER_PERSON", False),
                )
                flash(
                    "Sikeres foglalás! A visszaigazolást hamarosan küldjük.", "success"
                )
                return redirect(url_for("guest.my_bookings"))
            except ValueError as e:
                flash(str(e), "danger")
                return redirect(url_for("guest.index"))

        # Fallback útvonal: közvetlen form-adatból
        current_app.logger.warning(
            "Booking form validate failed; form.errors=%s, formdata=%s",
            getattr(form, "errors", None),
            request.form,
        )
        try:
            room_id = request.form.get("room_id")
            arrival = request.form.get("arrival_date")
            departure = request.form.get("departure_date")
            guests_field = request.form.get("guests")
            if not room_id or not arrival or not departure:
                raise ValueError("Missing booking fields")

            check_in = datetime.strptime(arrival, "%Y-%m-%d")
            check_out = datetime.strptime(departure, "%Y-%m-%d")
            guests_count = int(guests_field) if guests_field else 1

            create_booking(
                user_id=current_user.id,
                room_id=int(room_id),
                check_in=check_in,
                check_out=check_out,
                guests_count=guests_count,
                price_per_person=current_app.config.get("PRICE_PER_PERSON", False),
            )
            flash(
                "Sikeres foglalás! (fallback útvonal) A visszaigazolást hamarosan küldjük.",
                "success",
            )
            return redirect(url_for("guest.my_bookings"))
        except ValueError as e:
            current_app.logger.exception("Booking fallback failed")
            flash(f"Hiba a foglalás során: {e}", "danger")
            return redirect(url_for("guest.index"))
    except Exception as e:
        current_app.logger.exception("Unhandled error in book_room")
        flash(f"Hiba a foglalás során: {e}", "danger")
        return redirect(url_for("guest.index"))


@guest_bp.route("/booking/<int:booking_id>/add-service", methods=["GET", "POST"])
@login_required
def order_service(booking_id):
    """Kiegészítő szolgáltatás rendelése az aktív foglaláshoz"""
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != current_user.id or booking.status == BookingStatus.cancelled:
        flash("Ehhez a foglaláshoz nem rendelhető szolgáltatás.", "danger")
        return redirect(url_for("guest.my_bookings"))

    form = GuestServiceOrderForm()

    if form.validate_on_submit():
        service = ExtraService.query.get_or_404(form.service_id.data)

        # 1. Kapcsoló tábla frissítése
        new_service = BookingService(
            booking_id=booking.id, service_id=service.id, quantity=form.quantity.data
        )
        db.session.add(new_service)

        # 2. Számla és foglalás összegének növelése
        extra_cost = service.price * form.quantity.data
        booking.total_price += extra_cost

        if booking.invoice:
            booking.invoice.total_amount += extra_cost

        db.session.commit()
        flash(
            f"Sikeresen megrendelte a következő szolgáltatást: {service.name}",
            "success",
        )
        return redirect(url_for("guest.my_bookings"))

    form.booking_id.data = booking.id
    return render_template("order_service.html", form=form, booking=booking)


@guest_bp.route("/my-bookings")
@login_required
def my_bookings():
    """A vendég saját foglalásainak listázása"""
    bookings = (
        Booking.query.filter_by(user_id=current_user.id)
        .order_by(Booking.created_at.desc())
        .all()
    )
    return render_template("my_bookings.html", bookings=bookings)


@guest_bp.route("/booking/<int:booking_id>/cancel", methods=["GET", "POST"])
@login_required
def cancel_booking(booking_id):
    """Foglalás lemondása a vendég által"""
    booking = Booking.query.get_or_404(booking_id)

    # Biztonsági ellenőrzés: csak a saját foglalását mondhatja le
    if booking.user_id != current_user.id:
        abort(403)

    form = BookingCancelForm()
    if form.validate_on_submit() and form.confirm.data:
        booking.cancel()
        db.session.commit()
        flash("A foglalás sikeresen le lett mondva.", "info")
        return redirect(url_for("guest.my_bookings"))

    return render_template("cancel_booking.html", form=form, booking=booking)


@guest_bp.route("/booking/<int:booking_id>/edit", methods=["GET", "POST"])
@login_required
def edit_booking(booking_id):
    """Vendég számára foglalás módosítása (dátumok, vendégek száma)."""
    booking = Booking.query.get_or_404(booking_id)

    # Csak a saját, nem lemondott foglalását szerkesztheti a vendég
    if booking.user_id != current_user.id:
        abort(403)
    if booking.status == BookingStatus.cancelled:
        flash("A lemondott foglalást nem lehet szerkeszteni.", "warning")
        return redirect(url_for("guest.my_bookings"))

    form = BookingEditForm()

    if form.validate_on_submit():
        try:
            new_check_in = datetime.combine(form.arrival_date.data, datetime.min.time())
            new_check_out = datetime.combine(
                form.departure_date.data, datetime.min.time()
            )

            # Validáljuk a logikát: távozás > érkezés
            if new_check_out <= new_check_in:
                flash(
                    "A távozás dátuma később kell legyen, mint az érkezés dátuma.",
                    "danger",
                )
                return render_template("edit_booking.html", form=form, booking=booking)

            # Ellenőrizzük az ütközéseket, kizárva az aktuális foglalást
            if Booking.has_conflict(
                booking.room_id,
                new_check_in,
                new_check_out,
                exclude_booking_id=booking.id,
            ):
                flash("A megadott időszak ütközik egy másik foglalással.", "danger")
                return render_template("edit_booking.html", form=form, booking=booking)

            # Frissítjük a foglalás adatait
            booking.check_in = new_check_in
            booking.check_out = new_check_out
            booking.guests_count = form.guests.data

            # Új ár kiszámítása (nem számoljuk bele az extra szolgáltatásokat itt)
            from ..services.booking_service import calculate_total_price

            booking.total_price = calculate_total_price(
                booking.room,
                new_check_in,
                new_check_out,
                guests_count=booking.guests_count,
                price_per_person=current_app.config.get("PRICE_PER_PERSON", False),
            )
            if booking.invoice:
                booking.invoice.total_amount = booking.total_price

            db.session.commit()
            flash("A foglalás sikeresen frissítve.", "success")
            return redirect(url_for("guest.my_bookings"))
        except Exception as e:
            current_app.logger.exception("Error updating booking")
            flash(f"Hiba a foglalás frissítése során: {e}", "danger")
            return render_template("edit_booking.html", form=form, booking=booking)

    # GET -> Kitöltjük az űrlapot az aktuális értékekkel
    if request.method == "GET":
        form.arrival_date.data = booking.check_in.date()
        form.departure_date.data = booking.check_out.date()
        form.guests.data = getattr(booking, "guests_count", 1)

    return render_template("edit_booking.html", form=form, booking=booking)

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from functools import wraps

from .. import db
from ..models import Room, Role, Booking
from ..forms.admin_forms import RoomForm, RoomDeleteForm
from ..forms.reception_forms import BookingActionForm
from ..services.admin_service import (
    create_room_from_form,
    update_room_from_form,
    delete_room as service_delete_room,
)
from flask import current_app

admin_bp = Blueprint("admin", __name__)


# --- BIZTONSÁGI DEKORÁTOR ---
def admin_required(f):
    """Kizárólag adminisztrátorok engedélyezése"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != Role.admin:
            abort(403)  # 403 Forbidden hiba
        return f(*args, **kwargs)

    return decorated_function


# --- ÚTVONALAK ---


@admin_bp.route("/dashboard")
@login_required
@admin_required
def admin_dashboard():
    """Az összes szoba listázása állapotokkal"""
    # A szobákat szobaszám szerint sorba rendezve kérjük le
    rooms = Room.query.order_by(Room.room_number).all()
    return render_template("admin_dashboard.html", rooms=rooms)


@admin_bp.route("/room/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_room():
    """Új szoba felvétele az adatbázisba"""
    form = RoomForm()

    if form.validate_on_submit():
        try:
            new_room = create_room_from_form(form)
            flash(f"{new_room.room_number}. szoba sikeresen hozzáadva!", "success")
            return redirect(url_for("admin.admin_dashboard"))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template(
        "admin_room_form.html", form=form, title="Új szoba hozzáadása"
    )


@admin_bp.route("/room/<int:room_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_room(room_id):
    """Meglévő szoba adatainak szerkesztése"""
    room = Room.query.get_or_404(room_id)
    form = RoomForm()

    if form.validate_on_submit():
        try:
            update_room_from_form(room, form)
            flash(f"A {room.room_number}. szoba adatai frissültek.", "success")
            return redirect(url_for("admin.admin_dashboard"))
        except ValueError as e:
            flash(str(e), "danger")
            return render_template(
                "admin_room_form.html", form=form, room=room, title="Szoba szerkesztése"
            )

    elif request.method == "GET":
        # Form előtöltése a jelenlegi adatokkal
        form.room_number.data = room.room_number
        form.capacity.data = room.capacity
        form.price_per_night.data = room.price_per_night
        form.equipment.data = room.equipment
        form.description.data = room.description
        form.status.data = room.status.name  # Enum stringgé alakítása a legördülőhöz

    return render_template(
        "admin_room_form.html", form=form, room=room, title="Szoba szerkesztése"
    )


@admin_bp.route("/room/<int:room_id>/delete", methods=["GET", "POST"])
@login_required
@admin_required
def delete_room(room_id):
    """Szoba végleges törlése"""
    room = Room.query.get_or_404(room_id)
    form = RoomDeleteForm()
    if form.validate_on_submit():
        try:
            deleted_number = service_delete_room(room)
            flash(
                f"A {deleted_number}. szoba véglegesen törölve lett a rendszerből.",
                "warning",
            )
            return redirect(url_for("admin.admin_dashboard"))
        except ValueError as e:
            flash(str(e), "danger")
            return redirect(url_for("admin.delete_room", room_id=room.id))
        except Exception:
            current_app.logger.exception("Error deleting room")
            flash(
                "Hiba történt a szoba törlése közben. Részletek a naplóban.",
                "danger",
            )
            return redirect(url_for("admin.admin_dashboard"))

    return render_template("admin_delete_room.html", form=form, room=room)


@admin_bp.route("/bookings")
@login_required
@admin_required
def admin_bookings():
    """Listázza az összes foglalást az admin számára és biztosít művelet végrehajtást."""
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()

    # Készítsünk külön BookingActionForm példányt minden foglaláshoz,
    # hogy a sablon egyszerűen renderelhesse őket (és legyen CSRF tokenjük).
    forms = {b.id: BookingActionForm() for b in bookings}
    for b in bookings:
        forms[b.id].booking_id.data = b.id

    return render_template("admin_bookings.html", bookings=bookings, forms=forms)


@admin_bp.route("/booking/<int:booking_id>/action", methods=["POST"])
@login_required
@admin_required
def booking_action(booking_id):
    form = BookingActionForm()
    if not form.validate_on_submit():
        flash("Érvénytelen kérés.", "danger")
        return redirect(url_for("admin.admin_bookings"))

    booking = Booking.query.get_or_404(booking_id)
    action = form.action.data
    try:
        if action == "confirm":
            booking.confirm()
            db.session.commit()
            flash("Foglalás visszaigazolva.", "success")
        elif action == "cancel":
            booking.cancel()
            db.session.commit()
            flash("Foglalás lemondva.", "info")
        elif action == "check_in":
            booking.check_in_action()
            db.session.commit()
            flash("Vendég bejelentkezett.", "success")
        elif action == "check_out":
            booking.check_out_action()
            db.session.commit()
            flash("Vendég kijelentkeztetve.", "success")
        else:
            flash("Ismeretlen művelet.", "warning")
    except Exception as e:
        current_app.logger.exception("Admin booking action failed")
        flash(f"Hiba a művelet során: {e}", "danger")

    return redirect(url_for("admin.admin_bookings"))

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from ..utils.rbac import roles_required

from .. import db
from ..models import Room, Role, Booking, User, Permission, RolePermission, BookingStatus, ExtraService
from ..services.reception_service import perform_booking_action, add_extra_service_to_booking
from ..forms.admin_forms import RoomForm, RoomDeleteForm
from ..forms.reception_forms import BookingActionForm
from ..forms.admin_forms import BookingServiceAddForm
from ..services.admin_service import (
    create_room_from_form,
    update_room_from_form,
    delete_room as service_delete_room,
)
from flask import current_app
from ..forms.admin_forms import UserRoleForm, PermissionForm
from ..forms.admin_forms import AdminCreateServiceForm, ServiceDeleteForm

admin_bp = Blueprint("admin", __name__)


# Use centralized `roles_required` decorator for admin-only routes


# --- ÚTVONALAK ---


@admin_bp.route("/dashboard")
@login_required
@roles_required(Role.admin)
def admin_dashboard():
    """Az összes szoba listázása állapotokkal"""
    # A szobákat szobaszám szerint sorba rendezve kérjük le
    rooms = Room.query.order_by(Room.room_number).all()
    return render_template("admin_dashboard.html", rooms=rooms)


@admin_bp.route("/room/add", methods=["GET", "POST"])
@login_required
@roles_required(Role.admin)
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
@roles_required(Role.admin)
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
@roles_required(Role.admin)
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
@roles_required(Role.admin)
def admin_bookings():
    """Listázza az összes foglalást az admin számára és biztosít művelet végrehajtást."""
    # Hide cancelled and checked-out bookings from admin listing as well
    excluded = [BookingStatus.cancelled, BookingStatus.checked_out]
    bookings = Booking.query.filter(~Booking.status.in_(excluded)).order_by(Booking.created_at.desc()).all()

    # Készítsünk külön BookingActionForm és BookingServiceAddForm példányt minden foglaláshoz,
    # hogy a sablon egyszerűen renderelhesse őket (és legyen CSRF tokenjük).
    forms = {b.id: BookingActionForm() for b in bookings}
    service_forms = {}
    for b in bookings:
        forms[b.id].booking_id.data = b.id
        sf = BookingServiceAddForm()
        sf.booking_id.data = b.id
        service_forms[b.id] = sf

    return render_template("admin_bookings.html", bookings=bookings, forms=forms, service_forms=service_forms)


@admin_bp.route("/users")
@login_required
@roles_required(Role.admin)
def admin_users():
    users = User.query.order_by(User.username).all()
    return render_template("admin_users.html", users=users)


@admin_bp.route("/user/<int:user_id>/edit-role", methods=["GET", "POST"])
@login_required
@roles_required(Role.admin)
def edit_user_role(user_id):
    user = User.query.get_or_404(user_id)
    form = UserRoleForm()
    if form.validate_on_submit():
        try:
            user.role = Role[form.role.data]
            db.session.commit()
            flash("Szerepkör frissítve.", "success")
            return redirect(url_for("admin.admin_users"))
        except Exception as e:
            db.session.rollback()
            flash(f"Hiba a szerepkör mentésekor: {e}", "danger")

    elif request.method == "GET":
        form.role.data = user.role.name

    return render_template("admin_edit_user.html", user=user, form=form)


@admin_bp.route("/permissions", methods=["GET", "POST"])
@login_required
@roles_required(Role.admin)
def admin_permissions():
    # Replace Permissions UI with Admin Service-order UI
    from ..forms.admin_forms import AdminServiceForm

    form = AdminServiceForm()

    # populate choices dynamically
    bookings = Booking.query.filter(~Booking.status.in_([BookingStatus.cancelled, BookingStatus.checked_out])).order_by(Booking.created_at.desc()).all()
    form.booking_id.choices = [(b.id, f"#{b.id} - {b.user.username if b.user else b.user_id} ({b.room.room_number if b.room else b.room_id})") for b in bookings]
    services = ExtraService.query.order_by(ExtraService.name).all()
    form.service_id.choices = [(s.id, f"{s.name} ({s.price} Ft)") for s in services]

    if form.validate_on_submit():
        booking = Booking.query.get_or_404(form.booking_id.data)
        try:
            add_extra_service_to_booking(booking, form.service_id.data, form.quantity.data)
            flash(f"{form.quantity.data}x szolgáltatás hozzáadva a #{booking.id} foglaláshoz.", "success")
            return redirect(url_for("admin.admin_permissions"))
        except Exception as e:
            db.session.rollback()
            flash(f"Hiba hozzáadáskor: {e}", "danger")

    return render_template("admin_permissions.html", form=form, bookings=bookings, services=services)


@admin_bp.route("/services", methods=["GET", "POST"])
@login_required
@roles_required(Role.admin)
def admin_services():
    """Admin CRUD for ExtraService (list, create)."""
    form = AdminCreateServiceForm()
    delete_form = ServiceDeleteForm()
    services = ExtraService.query.order_by(ExtraService.name).all()

    if form.validate_on_submit():
        try:
            new = ExtraService(name=form.name.data.strip(), description=form.description.data.strip() if form.description.data else None, price=form.price.data)
            db.session.add(new)
            db.session.commit()
            flash("Szolgáltatás létrehozva.", "success")
            return redirect(url_for("admin.admin_services"))
        except Exception as e:
            db.session.rollback()
            flash(f"Hiba: {e}", "danger")

    return render_template("admin_services.html", services=services, form=form, delete_form=delete_form)


@admin_bp.route("/service/<int:service_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required(Role.admin)
def edit_service(service_id):
    s = ExtraService.query.get_or_404(service_id)
    form = AdminCreateServiceForm()
    if form.validate_on_submit():
        s.name = form.name.data.strip()
        s.description = form.description.data.strip() if form.description.data else None
        s.price = form.price.data
        db.session.commit()
        flash("Szolgáltatás frissítve.", "success")
        return redirect(url_for("admin.admin_services"))
    elif request.method == "GET":
        form.name.data = s.name
        form.description.data = s.description
        form.price.data = s.price

    return render_template("admin_service_form.html", form=form, service=s)


@admin_bp.route("/service/<int:service_id>/delete", methods=["POST"]) 
@login_required
@roles_required(Role.admin)
def delete_service(service_id):
    s = ExtraService.query.get_or_404(service_id)
    try:
        db.session.delete(s)
        db.session.commit()
        flash("Szolgáltatás törölve.", "warning")
    except Exception as e:
        db.session.rollback()
        flash(f"Hiba törléskor: {e}", "danger")
    return redirect(url_for("admin.admin_services"))


@admin_bp.route("/booking/<int:booking_id>/action", methods=["POST"])
@login_required
@roles_required(Role.admin)
def booking_action(booking_id):
    form = BookingActionForm()
    if not form.validate_on_submit():
        flash("Érvénytelen kérés.", "danger")
        return redirect(url_for("admin.admin_bookings"))

    booking = Booking.query.get_or_404(booking_id)
    action = form.action.data
    # Disallow acting on already-closed bookings
    from ..models import BookingStatus as _BookingStatus

    if booking.status in (_BookingStatus.cancelled, _BookingStatus.checked_out):
        flash("Ezen a foglaláson nem végezhető művelet (lezárt vagy lemondott).", "warning")
        return redirect(url_for("admin.admin_bookings"))

    try:
        # Use same service to ensure consistent side-effects (room status, invoice, audit)
        perform_booking_action(booking, action)
        # user feedback
        if action == "confirm":
            flash("Foglalás visszaigazolva.", "success")
        elif action == "cancel":
            flash("Foglalás lemondva.", "info")
        elif action == "check_in":
            flash("Vendég bejelentkezett.", "success")
        elif action == "check_out":
            flash("Vendég kijelentkeztetve.", "success")
        else:
            flash("Művelet végrehajtva.", "success")
    except Exception as e:
        current_app.logger.exception("Admin booking action failed")
        flash(f"Hiba a művelet során: {e}", "danger")

    return redirect(url_for("admin.admin_bookings"))


@admin_bp.route("/booking/<int:booking_id>/add_service", methods=["POST"]) 
@login_required
@roles_required(Role.admin)
def booking_add_service(booking_id):
    form = BookingServiceAddForm()
    if not form.validate_on_submit():
        flash("Érvénytelen szolgáltatás kérés.", "danger")
        return redirect(url_for("admin.admin_bookings"))

    booking = Booking.query.get_or_404(booking_id)
    try:
        add_extra_service_to_booking(booking, form.service_id.data, form.quantity.data)
        flash("Szolgáltatás hozzáadva a foglaláshoz.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Hiba hozzáadáskor: {e}", "danger")

    return redirect(url_for("admin.admin_bookings"))

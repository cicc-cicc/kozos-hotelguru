from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from functools import wraps

from ..models import Booking, Role, BookingStatus
from ..forms.reception_forms import BookingActionForm, ServiceOrderForm
from ..services.reception_service import (
    perform_booking_action,
    add_extra_service_to_booking,
)

reception_bp = Blueprint("reception", __name__)


# --- BIZTONSÁGI DEKORÁTOR ---
def receptionist_required(f):
    """Csak recepciósok vagy adminok engedélyezése"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in [
            Role.receptionist,
            Role.admin,
        ]:
            abort(403)  # 403 Forbidden hiba
        return f(*args, **kwargs)

    return decorated_function


# --- ÚTVONALAK ---


@reception_bp.route("/dashboard")
@login_required
@receptionist_required
def reception_dashboard():
    """Az összes foglalás listázása, szűrési lehetőséggel"""
    # Szűrési paraméter lekérése az URL-ből (pl. ?status=pending)
    status_filter = request.args.get("status")

    query = Booking.query

    if status_filter:
        try:
            status_enum = BookingStatus[status_filter]
            query = query.filter(Booking.status == status_enum)
        except KeyError:
            pass  # Ha érvénytelen a státusz a linkben, ignoráljuk

    # Foglalások rendezése érkezés szerint
    bookings = query.order_by(Booking.check_in.asc()).all()

    # Létrehozzuk az űrlapot a státuszváltó gombokhoz
    action_form = BookingActionForm()

    return render_template(
        "reception_dashboard.html", bookings=bookings, action_form=action_form
    )


@reception_bp.route("/booking/<int:booking_id>/action", methods=["POST"])
@login_required
@receptionist_required
def handle_booking(booking_id):
    """Foglalás állapotának frissítése (Visszaigazolás, Check-in, Check-out)"""
    booking = Booking.query.get_or_404(booking_id)
    form = BookingActionForm()

    if form.validate_on_submit():
        action = form.action.data
        try:
            perform_booking_action(booking, action)
            flash("Művelet sikeresen végrehajtva.", "success")
        except ValueError as e:
            flash(str(e), "danger")

    return redirect(url_for("reception.reception_dashboard"))


@reception_bp.route("/booking/<int:booking_id>/add-service", methods=["GET", "POST"])
@login_required
@receptionist_required
def add_extra_service(booking_id):
    """Recepciós manuális szolgáltatás-hozzáadása a vendég számlájához"""
    booking = Booking.query.get_or_404(booking_id)

    # Ha a foglalás már le van zárva, ne adjunk hozzá extra tételt
    if booking.status in [BookingStatus.cancelled, BookingStatus.checked_out]:
        flash("Lezárt vagy lemondott foglaláshoz nem adható szolgáltatás.", "danger")
        return redirect(url_for("reception.reception_dashboard"))

    form = ServiceOrderForm()

    if form.validate_on_submit():
        try:
            add_extra_service_to_booking(
                booking, form.service_id.data, form.quantity.data
            )
            flash(
                f"{form.quantity.data}x hozzáadva a #{booking.id} számlájához.",
                "success",
            )
            return redirect(url_for("reception.reception_dashboard"))
        except ValueError as e:
            flash(str(e), "danger")

    form.booking_id.data = booking.id
    return render_template("reception_add_service.html", form=form, booking=booking)

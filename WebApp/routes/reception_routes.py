from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from ..utils.rbac import roles_required

from ..models import Booking, Role, BookingStatus
from ..forms.reception_forms import BookingActionForm, ServiceOrderForm
from ..services.reception_service import (
    perform_booking_action,
    add_extra_service_to_booking,
)

reception_bp = Blueprint("reception", __name__)


# --- BIZTONSÁGI DEKORÁTOR ---
# Use `roles_required` from WebApp.utils.rbac for role checks


# --- ÚTVONALAK ---


@reception_bp.route("/dashboard")
@login_required
@roles_required(Role.receptionist, Role.admin)
def reception_dashboard():
    """Az összes foglalás listázása, szűrési lehetőséggel"""
    # Szűrési paraméter lekérése az URL-ből (pl. ?status=pending)
    status_filter = request.args.get("status")

    # By default exclude cancelled and checked_out bookings from lists
    excluded = [BookingStatus.cancelled, BookingStatus.checked_out]

    query = Booking.query
    if status_filter:
        try:
            status_enum = BookingStatus[status_filter]
            # Disallow listing fully closed statuses in the dashboard
            if status_enum in excluded:
                # return empty list when requesting excluded status
                bookings = []
                return render_template(
                    "receptiondashboard.html",
                    bookings=bookings,
                    action_form=BookingActionForm(),
                )
            query = query.filter(Booking.status == status_enum)
        except KeyError:
            pass
    else:
        query = query.filter(~Booking.status.in_(excluded))

    # Foglalások rendezése érkezés szerint
    bookings = query.order_by(Booking.check_in.asc()).all()

    # Létrehozzuk az űrlapot a státuszváltó gombokhoz
    action_form = BookingActionForm()

    # counts for quick overview
    counts = {
        "all": Booking.query.count(),
        "pending": Booking.query.filter(
            Booking.status == BookingStatus.pending
        ).count(),
        "confirmed": Booking.query.filter(
            Booking.status == BookingStatus.confirmed
        ).count(),
        "checked_in": Booking.query.filter(
            Booking.status == BookingStatus.checked_in
        ).count(),
    }

    return render_template(
        "receptiondashboard.html",
        bookings=bookings,
        action_form=action_form,
        counts=counts,
    )


@reception_bp.route("/booking/<int:booking_id>/action", methods=["POST"])
@login_required
@roles_required(Role.receptionist, Role.admin)
def handle_booking(booking_id):
    """Foglalás állapotának frissítése (Visszaigazolás, Check-in, Check-out)"""
    booking = Booking.query.get_or_404(booking_id)
    form = BookingActionForm()

    if form.validate_on_submit():
        action = form.action.data
        try:
            perform_booking_action(booking, action)
            flash("Művelet sikeresen végrehajtva.", "success")
            # refresh booking from DB to get updated status
            booking = Booking.query.get(booking_id)
            try:
                new_status = booking.status.name
                if new_status in ("cancelled", "checked_out"):
                    return redirect(url_for("reception.reception_dashboard"))
                return redirect(
                    url_for("reception.reception_dashboard", status=new_status)
                )
            except Exception:
                return redirect(url_for("reception.reception_dashboard"))
        except ValueError as e:
            flash(str(e), "danger")

    return redirect(url_for("reception.reception_dashboard"))


@reception_bp.route("/booking/<int:booking_id>/add-service", methods=["GET", "POST"])
@login_required
@roles_required(Role.receptionist, Role.admin)
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
    return render_template("receptionaddservice.html", form=form, booking=booking)

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


# --- ÚTVONALAK ---


@reception_bp.route("/dashboard")
@login_required
@roles_required(Role.receptionist, Role.admin)
def reception_dashboard():
    """Az összes foglalás listázása, szűrési lehetőséggel"""
    status_filter = request.args.get("status")

    # Alapértelmezés szerint a lemondott és kijelentkezett foglalásokat nem listázzuk
    excluded = [BookingStatus.cancelled, BookingStatus.checked_out]

    query = Booking.query
    if status_filter:
        try:
            status_enum = BookingStatus[status_filter]
            if status_enum in excluded:
                bookings = []
                # (JAVÍTVA: mappa előtag és fájlnév)
                return render_template(
                    "reception/reception_dashboard.html",
                    bookings=bookings,
                    action_form=BookingActionForm(),
                )
            query = query.filter(Booking.status == status_enum)
        except KeyError:
            pass
    else:
        query = query.filter(~Booking.status.in_(excluded))

    bookings = query.order_by(Booking.check_in.asc()).all()
    action_form = BookingActionForm()

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

    # (JAVÍTVA: mappa előtag és fájlnév)
    return render_template(
        "reception/reception_dashboard.html",
        bookings=bookings,
        action_form=action_form,
        counts=counts,
    )


@reception_bp.route("/booking/<int:booking_id>/action", methods=["POST"])
@login_required
@roles_required(Role.receptionist, Role.admin)
def handle_booking(booking_id):
    """Foglalás állapotának frissítése"""
    booking = Booking.query.get_or_404(booking_id)
    form = BookingActionForm()

    if form.validate_on_submit():
        action = form.action.data
        try:
            perform_booking_action(booking, action)
            flash("Művelet sikeresen végrehajtva.", "success")
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
    """Szolgáltatás hozzáadása a számlához"""
    booking = Booking.query.get_or_404(booking_id)

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
    # (JAVÍTVA: mappa előtag és fájlnév)
    return render_template(
        "reception/reception_add_service.html", form=form, booking=booking
    )
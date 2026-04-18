from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from functools import wraps

from .. import db
from ..models import Booking, Room, ExtraService, BookingService, Role, BookingStatus
from ..forms.reception_forms import BookingActionForm, ServiceOrderForm

reception_bp = Blueprint('reception', __name__)

# --- BIZTONSÁGI DEKORÁTOR ---
def receptionist_required(f):
    """Csak recepciósok vagy adminok engedélyezése"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in [Role.receptionist, Role.admin]:
            abort(403) # 403 Forbidden hiba
        return f(*args, **kwargs)
    return decorated_function

# --- ÚTVONALAK ---

@reception_bp.route('/dashboard')
@login_required
@receptionist_required
def reception_dashboard():
    """Az összes foglalás listázása, szűrési lehetőséggel"""
    # Szűrési paraméter lekérése az URL-ből (pl. ?status=pending)
    status_filter = request.args.get('status')
    
    query = Booking.query
    
    if status_filter:
        try:
            status_enum = BookingStatus[status_filter]
            query = query.filter(Booking.status == status_enum)
        except KeyError:
            pass # Ha érvénytelen a státusz a linkben, ignoráljuk
            
    # Foglalások rendezése érkezés szerint
    bookings = query.order_by(Booking.check_in.asc()).all()
    
    # Létrehozzuk az űrlapot a státuszváltó gombokhoz
    action_form = BookingActionForm()
    
    return render_template('reception_dashboard.html', bookings=bookings, action_form=action_form)


@reception_bp.route('/booking/<int:booking_id>/action', methods=['POST'])
@login_required
@receptionist_required
def handle_booking(booking_id):
    """Foglalás állapotának frissítése (Visszaigazolás, Check-in, Check-out)"""
    booking = Booking.query.get_or_404(booking_id)
    form = BookingActionForm()
    
    if form.validate_on_submit():
        action = form.action.data
        try:
            if action == 'confirm':
                booking.confirm() # A modeled ütközés-ellenőrzését is futtatja!
                flash(f'Foglalás (#{booking.id}) visszaigazolva.', 'success')
                
            elif action == 'check_in':
                booking.check_in_action()
                flash(f'Vendég bejelentkeztetve: Foglalás #{booking.id}.', 'success')
                
            elif action == 'check_out':
                booking.check_out_action()
                # Számla lezárása (kifizetve)
                if booking.invoice:
                    booking.invoice.paid = True
                flash(f'Kijelentkezés és számlázás befejezve (Foglalás #{booking.id}).', 'info')
                
            elif action == 'cancel':
                booking.cancel()
                flash(f'Foglalás (#{booking.id}) lemondva.', 'warning')
                
            db.session.commit()
            
        except ValueError as e:
            # Ha pl. a confirm() ütközést talál, elkapjuk a ValueError-t
            flash(str(e), 'danger')
            
    return redirect(url_for('reception.reception_dashboard'))


@reception_bp.route('/booking/<int:booking_id>/add-service', methods=['GET', 'POST'])
@login_required
@receptionist_required
def add_extra_service(booking_id):
    """Recepciós manuális szolgáltatás-hozzáadása a vendég számlájához"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Ha a foglalás már le van zárva, ne adjunk hozzá extra tételt
    if booking.status in [BookingStatus.cancelled, BookingStatus.checked_out]:
        flash('Lezárt vagy lemondott foglaláshoz nem adható szolgáltatás.', 'danger')
        return redirect(url_for('reception.reception_dashboard'))
        
    form = ServiceOrderForm()
    
    if form.validate_on_submit():
        service = ExtraService.query.get_or_404(form.service_id.data)
        quantity = form.quantity.data
        
        # Kapcsolótábla bejegyzés
        new_service = BookingService(booking_id=booking.id, service_id=service.id, quantity=quantity)
        db.session.add(new_service)
        
        # Pénzügyi adatok frissítése
        extra_cost = service.price * quantity
        booking.total_price += extra_cost
        if booking.invoice:
            booking.invoice.total_amount += extra_cost
            
        db.session.commit()
        flash(f'{quantity}x {service.name} hozzáadva a #{booking.id} számlájához.', 'success')
        return redirect(url_for('reception.reception_dashboard'))
        
    form.booking_id.data = booking.id
    return render_template('reception_add_service.html', form=form, booking=booking)
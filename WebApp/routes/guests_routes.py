from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from datetime import datetime

from .. import db
from ..models import Room, Booking, Invoice, BookingStatus, ExtraService, BookingService
from ..forms.booking_forms import RoomSearchForm, BookingRequestForm, BookingCancelForm
from ..forms.service_forms import GuestServiceOrderForm

# Blueprint létrehozása 'guest' néven
guest_bp = Blueprint('guest', __name__)

@guest_bp.route('/', methods=['GET', 'POST'])
def index():
    """Főoldal és szobakeresés indítása"""
    form = RoomSearchForm()
    
    if form.validate_on_submit():
        # A keresési adatokat URL paraméterként átadjuk a találati oldalnak
        return redirect(url_for('guest.search_results', 
                                arrival=form.arrival_date.data.strftime('%Y-%m-%d'), 
                                departure=form.departure_date.data.strftime('%Y-%m-%d'),
                                guests=form.guests.data))
                                
    # Alapértelmezett kezdőképernyő a keresővel
    return render_template('index.html', form=form)


@guest_bp.route('/search-results')
def search_results():
    """Szabad szobák listázása a megadott paraméterek alapján"""
    arrival_str = request.args.get('arrival')
    departure_str = request.args.get('departure')
    guests = request.args.get('guests', type=int)
    
    if not arrival_str or not departure_str or not guests:
        flash('Érvénytelen keresési paraméterek!', 'warning')
        return redirect(url_for('guest.index'))
        
    check_in = datetime.strptime(arrival_str, '%Y-%m-%d')
    check_out = datetime.strptime(departure_str, '%Y-%m-%d')
    
    # 1. Lekérjük az összes szobát, amibe befér ennyi ember
    suitable_rooms = Room.query.filter(Room.capacity >= guests).all()
    
    # 2. Leszűrjük azokat, amik szabadok az adott időszakban
    available_rooms = [room for room in suitable_rooms if room.is_available_for(check_in, check_out)]
    
    # Készítünk egy foglalási formot, amit majd a sablonban használunk
    booking_form = BookingRequestForm()
    booking_form.arrival_date.data = arrival_str
    booking_form.departure_date.data = departure_str
    
    return render_template('search_results.html', 
                           rooms=available_rooms, 
                           check_in=check_in, 
                           check_out=check_out, 
                           guests=guests,
                           form=booking_form)


@guest_bp.route('/book-room', methods=['POST'])
@login_required # Foglalni csak bejelentkezve lehet
def book_room():
    """Foglalás rögzítése és számla (Invoice) generálása"""
    form = BookingRequestForm()
    
    if form.validate_on_submit():
        room = Room.query.get_or_404(form.room_id.data)
        check_in = datetime.strptime(form.arrival_date.data, '%Y-%m-%d')
        check_out = datetime.strptime(form.departure_date.data, '%Y-%m-%d')
        
        # Dupla ellenőrzés a biztonság kedvéért (nehogy ketten foglalják le egyszerre)
        if not room.is_available_for(check_in, check_out):
            flash('Sajnáljuk, időközben ezt a szobát lefoglalták.', 'danger')
            return redirect(url_for('guest.index'))
            
        # Ár kiszámítása (éjszakák száma * ár)
        nights = max(1, (check_out - check_in).days)
        total_price = nights * room.price_per_night
        
        # 1. Foglalás létrehozása (alapból pending státusszal)
        new_booking = Booking(
            user_id=current_user.id,
            room_id=room.id,
            check_in=check_in,
            check_out=check_out,
            status=BookingStatus.pending,
            total_price=total_price
        )
        db.session.add(new_booking)
        db.session.flush() # Így megkapjuk a new_booking.id-t a számlához
        
        # 2. Számla (Invoice) létrehozása
        new_invoice = Invoice(
            booking_id=new_booking.id,
            total_amount=total_price,
            paid=False
        )
        db.session.add(new_invoice)
        db.session.commit()
        
        flash('Sikeres foglalás! A visszaigazolást hamarosan küldjük.', 'success')
        return redirect(url_for('guest.my_bookings'))
        
    flash('Hiba a foglalás során.', 'danger')
    return redirect(url_for('guest.index'))


@guest_bp.route('/my-bookings')
@login_required
def my_bookings():
    """A vendég saját foglalásainak listázása"""
    # Lekérjük a bejelentkezett vendég foglalásait, a legújabbakkal kezdve
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return render_template('my_bookings.html', bookings=bookings)


@guest_bp.route('/booking/<int:booking_id>/cancel', methods=['GET', 'POST'])
@login_required
def cancel_booking(booking_id):
    """Foglalás lemondása a vendég által"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Biztonsági ellenőrzés: csak a sajátját mondhatja le
    if booking.user_id != current_user.id:
        abort(403)
        
    form = BookingCancelForm()
    
    if form.validate_on_submit() and form.confirm.data:
        # A models.py-ban megírt metódust hívjuk
        booking.cancel() 
        db.session.commit()
        flash('A foglalás sikeresen le lett mondva.', 'info')
        return redirect(url_for('guest.my_bookings'))
        
    return render_template('cancel_booking.html', form=form, booking=booking)


@guest_bp.route('/booking/<int:booking_id>/add-service', methods=['GET', 'POST'])
@login_required
def order_service(booking_id):
    """Kiegészítő szolgáltatás rendelése az aktív foglaláshoz"""
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.user_id != current_user.id or booking.status == BookingStatus.cancelled:
        flash('Ehhez a foglaláshoz nem rendelhető szolgáltatás.', 'danger')
        return redirect(url_for('guest.my_bookings'))
        
    form = GuestServiceOrderForm()
    
    if form.validate_on_submit():
        service = ExtraService.query.get_or_404(form.service_id.data)
        
        # 1. Kapcsoló tábla frissítése
        new_service = BookingService(
            booking_id=booking.id,
            service_id=service.id,
            quantity=form.quantity.data
        )
        db.session.add(new_service)
        
        # 2. Számla és foglalás összegének növelése
        extra_cost = service.price * form.quantity.data
        booking.total_price += extra_cost
        
        if booking.invoice:
            booking.invoice.total_amount += extra_cost
            
        db.session.commit()
        flash(f'Sikeresen megrendelte a következő szolgáltatást: {service.name}', 'success')
        return redirect(url_for('guest.my_bookings'))
        
    form.booking_id.data = booking.id
    return render_template('order_service.html', form=form, booking=booking)
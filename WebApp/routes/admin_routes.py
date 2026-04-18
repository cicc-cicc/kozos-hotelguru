from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from functools import wraps

from .. import db
from ..models import Room, Role, RoomStatus
from ..forms.admin_forms import RoomForm, RoomDeleteForm

admin_bp = Blueprint('admin', __name__)

# --- BIZTONSÁGI DEKORÁTOR ---
def admin_required(f):
    """Kizárólag adminisztrátorok engedélyezése"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != Role.admin:
            abort(403) # 403 Forbidden hiba
        return f(*args, **kwargs)
    return decorated_function

# --- ÚTVONALAK ---

@admin_bp.route('/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """Az összes szoba listázása állapotokkal"""
    # A szobákat szobaszám szerint sorba rendezve kérjük le
    rooms = Room.query.order_by(Room.room_number).all()
    return render_template('admin_dashboard.html', rooms=rooms)


@admin_bp.route('/room/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_room():
    """Új szoba felvétele az adatbázisba"""
    form = RoomForm()
    
    if form.validate_on_submit():
        # Ellenőrizzük, hogy létezik-e már ez a szobaszám
        existing_room = Room.query.filter_by(room_number=form.room_number.data).first()
        if existing_room:
            flash(f'A {form.room_number.data} szobaszám már foglalt!', 'danger')
            return render_template('admin_room_form.html', form=form, title="Új szoba hozzáadása")
            
        new_room = Room(
            room_number=form.room_number.data,
            capacity=form.capacity.data,
            price_per_night=form.price_per_night.data,
            equipment=form.equipment.data,
            description=form.description.data
        )
        # Az enum állapot beállítása a models.py-ban megírt metódussal
        new_room.set_status(form.status.data)
        
        db.session.add(new_room)
        db.session.commit()
        flash(f'{new_room.room_number}. szoba sikeresen hozzáadva!', 'success')
        return redirect(url_for('admin.admin_dashboard'))
        
    return render_template('admin_room_form.html', form=form, title="Új szoba hozzáadása")


@admin_bp.route('/room/<int:room_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_room(room_id):
    """Meglévő szoba adatainak szerkesztése"""
    room = Room.query.get_or_404(room_id)
    form = RoomForm()
    
    if form.validate_on_submit():
        # Ellenőrizzük, hogy ha átírja a szobaszámot, az nem ütközik-e másikkal
        if form.room_number.data != room.room_number:
            existing = Room.query.filter_by(room_number=form.room_number.data).first()
            if existing:
                flash(f'A {form.room_number.data} szobaszám már létezik!', 'danger')
                return render_template('admin_room_form.html', form=form, room=room, title="Szoba szerkesztése")
                
        # Adatok frissítése
        room.room_number = form.room_number.data
        room.capacity = form.capacity.data
        room.price_per_night = form.price_per_night.data
        room.equipment = form.equipment.data
        room.description = form.description.data
        room.set_status(form.status.data)
        
        db.session.commit()
        flash(f'A {room.room_number}. szoba adatai frissültek.', 'success')
        return redirect(url_for('admin.admin_dashboard'))
        
    elif request.method == 'GET':
        # Form előtöltése a jelenlegi adatokkal
        form.room_number.data = room.room_number
        form.capacity.data = room.capacity
        form.price_per_night.data = room.price_per_night
        form.equipment.data = room.equipment
        form.description.data = room.description
        form.status.data = room.status.name # Enum stringgé alakítása a legördülőhöz
        
    return render_template('admin_room_form.html', form=form, room=room, title="Szoba szerkesztése")


@admin_bp.route('/room/<int:room_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_room(room_id):
    """Szoba végleges törlése"""
    room = Room.query.get_or_404(room_id)
    form = RoomDeleteForm()
    
    if form.validate_on_submit():
        # Figyelem: A models.py "cascade='all, delete-orphan'" beállítása miatt 
        # a szoba törlése a hozzá tartozó foglalásokat is törli!
        deleted_number = room.room_number
        db.session.delete(room)
        db.session.commit()
        flash(f'A {deleted_number}. szoba véglegesen törölve lett a rendszerből.', 'warning')
        return redirect(url_for('admin.admin_dashboard'))
        
    return render_template('admin_delete_room.html', form=form, room=room)
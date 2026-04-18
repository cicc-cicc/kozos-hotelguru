from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from .. import db
from ..models import User, Role
from ..forms.login_forms import LoginForm
from ..forms.registration_forms import RegistrationForm
from ..forms.profile_forms import UserProfileForm

# Blueprint létrehozása 'auth' néven
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Ha már be van lépve, ne regisztráljon újra
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        # Jelszó titkosítása mentés előtt
        hashed_password = generate_password_hash(form.password.data)
        
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password,
            phone=form.phone.data,
            address=form.address.data,
            role=Role.guest # Minden új regisztráló alapértelmezetten vendég
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Sikeres regisztráció! Most már bejelentkezhet.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        # Felhasználó ellenőrzése és jelszó validálása
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            flash(f'Üdvözöljük, {user.username}!', 'success')
            
            # Szerepkör alapú átirányítás a feladatleírásod szerint
            if user.role == Role.admin:
                return redirect(url_for('index')) # Ide jöhet később az admin oldal linkje
            elif user.role == Role.receptionist:
                return redirect(url_for('index')) # Ide jöhet később a recepciós oldal
            else:
                return redirect(url_for('index')) # Vendég átirányítása
        else:
            flash('Sikertelen bejelentkezés. Ellenőrizze a felhasználónevét és jelszavát!', 'danger')
            
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required # Csak bejelentkezett felhasználó tud kijelentkezni
def logout():
    logout_user()
    flash('Sikeresen kijelentkezett.', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required # Csak bejelentkezett felhasználó láthatja
def profile():
    form = UserProfileForm()
    
    if form.validate_on_submit():
        # Adatok frissítése az adatbázisban
        current_user.email = form.email.data
        current_user.phone = form.phone.data
        current_user.address = form.address.data
        db.session.commit()
        flash('Profil adatai sikeresen frissítve!', 'success')
        return redirect(url_for('auth.profile'))
        
    elif request.method == 'GET':
        # Ha csak megnyitja az oldalt, előre kitöltjük a meglévő adataival
        form.email.data = current_user.email
        form.phone.data = current_user.phone
        form.address.data = current_user.address
        
    return render_template('profile.html', form=form)
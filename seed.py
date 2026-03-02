import json
import os
from WebApp import create_app, db
from WebApp.models import User, Room

app = create_app()

def seed_database():
    with app.app_context():
        # Keressük meg a JSON fájlt
        json_path = os.path.join(os.path.dirname(__file__), 'data.json')
        
        if not os.path.exists(json_path):
            print(f"Hiba: Nem találom a fájlt itt: {json_path}")
            return

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print("Adatok betöltése folyamatban...")

        # 1. Felhasználók feltöltése
        for u_data in data.get('users', []):
            # Ellenőrizzük, létezik-e már a felhasználó
            exists = User.query.filter_by(username=u_data['username']).first()
            if not exists:
                # Csak azokat a mezőket adjuk át, amik benne vannak a modellben
                new_user = User(
                    username=u_data['username'],
                    email=u_data['email'],
                    role=u_data['role']
                )
                db.session.add(new_user)
                print(f"Felhasználó hozzáadva: {u_data['username']}")

        # 2. Szobák feltöltése
        for r_data in data.get('rooms', []):
            exists = Room.query.filter_by(room_number=r_data['room_number']).first()
            if not exists:
                new_room = Room(
                    room_number=r_data['room_number'],
                    capacity=r_data['capacity'],
                    price_per_night=r_data['price_per_night'],
                    is_available=r_data['is_available']
                )
                db.session.add(new_room)
                print(f"Szoba hozzáadva: {r_data['room_number']}")

        try:
            db.session.commit()
            print("\nSikeres feltöltés! Az adatbázis készen áll a használatra.")
        except Exception as e:
            db.session.rollback()
            print(f"\nHiba történt a mentés során: {e}")

if __name__ == '__main__':
    seed_database()
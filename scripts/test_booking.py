from datetime import datetime, timedelta
import json, os, sys

# Ensure project root is importable (so 'WebApp' package can be found)
proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from WebApp import create_app, db
from WebApp.models import User, Room

app = create_app()

with app.app_context():
    # Create test user if missing
    user = User.query.filter_by(username='test_robot').first()
    if not user:
        user = User(username='test_robot', email='test_robot@example.com', password_hash='x')
        db.session.add(user)
        db.session.commit()

    # Create test room if missing
    room = Room.query.filter_by(room_number='T100').first()
    if not room:
        room = Room(room_number='T100', capacity=2, price_per_night=5000.0, description='Test room')
        db.session.add(room)
        db.session.commit()

    # Prepare booking data
    arrival = datetime.utcnow().date()
    departure = arrival + timedelta(days=1)

    with app.test_client() as client:
        # Log in by manipulating session (Flask-Login stores _user_id)
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True

        # First, GET the search-results page to obtain a valid CSRF token
        params = {
            'arrival': arrival.strftime('%Y-%m-%d'),
            'departure': departure.strftime('%Y-%m-%d'),
            'guests': '2'
        }
        get_resp = client.get('/search-results', query_string=params)
        html = get_resp.get_data(as_text=True)

        # Extract CSRF token from HTML (input name="csrf_token")
        import re
        m = re.search(r'name="csrf_token"\s+type="hidden"\s+value="([^"]+)"', html)
        csrf = m.group(1) if m else None

        data = {
            'room_id': str(room.id),
            'arrival_date': arrival.strftime('%Y-%m-%d'),
            'departure_date': departure.strftime('%Y-%m-%d'),
            'guests': '2',
            'csrf_token': csrf,
            'submit': 'Foglalás véglegesítése'
        }

        resp = client.post('/book-room', data=data, follow_redirects=True)
        print('STATUS:', resp.status_code)
        print('LENGTH:', len(resp.data))
        # Print a snippet of response to inspect flashed messages
        text = resp.get_data(as_text=True)
        snippet = text[:1000]
        print('RESPONSE SNIPPET:\n', snippet)

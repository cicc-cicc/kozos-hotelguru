from datetime import datetime, timedelta
import os, sys, re
proj_root = os.path.dirname(os.path.abspath(__file__))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from WebApp import create_app, db
from WebApp.models import User, Room

app = create_app()

with app.app_context():
    user = User.query.filter_by(username="test_robot").first()
    if not user:
        user = User(username="test_robot", email="test_robot@example.com", password_hash="x")
        db.session.add(user)
        db.session.commit()
    room = Room.query.filter_by(room_number="T100").first()
    if not room:
        room = Room(room_number="T100", capacity=2, price_per_night=5000.0, description="Test room")
        db.session.add(room)
        db.session.commit()
    arrival = datetime.utcnow().date()
    departure = arrival + timedelta(days=1)

    client = app.test_client()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True

    params = {'arrival': arrival.strftime('%Y-%m-%d'), 'departure': departure.strftime('%Y-%m-%d'), 'guests': '2'}
    get_resp = client.get('/search-results', query_string=params)
    html = get_resp.get_data(as_text=True)
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    csrf = m.group(1) if m else None
    data = {
        'room_id': str(room.id),
        'arrival_date': arrival.strftime('%Y-%m-%d'),
        'departure_date': departure.strftime('%Y-%m-%d'),
        'guests': '2',
        'csrf_token': csrf
    }
    resp = client.post('/book-room', data=data, follow_redirects=True)
    text = resp.get_data(as_text=True)
    with open('tmp_response.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Wrote tmp_response.html, length=', len(text))

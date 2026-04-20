from datetime import datetime, timedelta
import json, os, sys

proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from WebApp import create_app, db
from WebApp.models import User, Booking

app = create_app()

with app.app_context():
    user = User.query.filter_by(username='test_robot').first()
    if not user:
        print('No test user found; run scripts/test_booking.py first')
        sys.exit(1)

    booking = Booking.query.filter_by(user_id=user.id).order_by(Booking.created_at.desc()).first()
    if not booking:
        print('No booking found for test_robot; run scripts/test_booking.py first')
        sys.exit(1)

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True

        # GET the edit page to fetch CSRF
        get_resp = client.get(f'/booking/{booking.id}/edit')
        html = get_resp.get_data(as_text=True)

        import re
        m = re.search(r'name="csrf_token"\s+type="hidden"\s+value="([^"]+)"', html)
        csrf = m.group(1) if m else None

        new_arrival = (booking.check_in.date() + timedelta(days=1)).strftime('%Y-%m-%d')
        new_departure = (booking.check_out.date() + timedelta(days=2)).strftime('%Y-%m-%d')

        data = {
            'arrival_date': new_arrival,
            'departure_date': new_departure,
            'guests': '1',
            'csrf_token': csrf,
            'submit': 'Foglalás frissítése'
        }

        resp = client.post(f'/booking/{booking.id}/edit', data=data, follow_redirects=True)
        print('STATUS:', resp.status_code)
        print('LENGTH:', len(resp.data))
        print('SNIPPET:\n', resp.get_data(as_text=True)[:1200])

from flask import Blueprint, jsonify, request
from flask_login import current_user
from flask import current_app
from ..models import Room, User
from .. import db
from ..services.booking_service import create_booking
from datetime import datetime
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

api_bp = Blueprint('api', __name__)


@api_bp.route('/rooms', methods=['GET'])
def api_rooms():
    """Get rooms

    Returns a list of rooms.
    ---
    responses:
      200:
        description: List of rooms
    """
    rooms = Room.query.all()
    data = [
        {
            'id': r.id,
            'room_number': r.room_number,
            'capacity': r.capacity,
            'price_per_night': r.price_per_night,
            'status': r.status.value if r.status else None,
            'equipment': r.equipment_list,
            'description': r.description,
        }
        for r in rooms
    ]
    return jsonify({'rooms': data})


@api_bp.route('/bookings', methods=['POST'])
@jwt_required(optional=True)
def api_create_booking():
    """Create a booking

    Expects JSON: {"room_id": int, "check_in": "YYYY-MM-DD", "check_out": "YYYY-MM-DD", "guests": int}
    ---
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            room_id:
              type: integer
            check_in:
              type: string
            check_out:
              type: string
            guests:
              type: integer
    responses:
      201:
        description: Booking created
      400:
        description: Invalid input
      401:
        description: Authentication required
    """
    data = request.get_json() or {}
    room_id = data.get('room_id')
    check_in_s = data.get('check_in')
    check_out_s = data.get('check_out')
    guests = data.get('guests', 1)

    if not room_id or not check_in_s or not check_out_s:
        return jsonify({'error': 'room_id, check_in and check_out are required'}), 400

    # Determine user: prefer JWT identity, fallback to provided user_id, else session
    jwt_identity = None
    try:
      jwt_identity = get_jwt_identity()
    except Exception:
      jwt_identity = None

    user_id = jwt_identity or data.get('user_id') or (current_user.get_id() if current_user and current_user.is_authenticated else None)
    if not user_id:
      return jsonify({'error': 'Authentication required or include user_id in payload'}), 401

    try:
        check_in = datetime.strptime(check_in_s, '%Y-%m-%d')
        check_out = datetime.strptime(check_out_s, '%Y-%m-%d')
    except Exception:
        return jsonify({'error': 'Invalid date format, use YYYY-MM-DD'}), 400

    try:
        booking, invoice = create_booking(
            user_id=int(user_id),
            room_id=int(room_id),
            check_in=check_in,
            check_out=check_out,
            guests_count=int(guests),
        )
        return jsonify({'booking_id': booking.id, 'invoice_id': invoice.id}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Server error', 'detail': str(e)}), 500



@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    """Login and receive access token

    Expects JSON: {"username": "...", "password": "..."}
    ---
    responses:
      200:
        description: Access token
      401:
        description: Invalid credentials
    """
    payload = request.get_json() or {}
    username = payload.get('username')
    password = payload.get('password')
    if not username or not password:
        return jsonify({'error': 'username and password required'}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid credentials'}), 401

    additional_claims = {'role': user.role.value if user.role else 'guest'}
    access_token = create_access_token(identity=user.id, additional_claims=additional_claims)
    return jsonify({'access_token': access_token, 'user_id': user.id})

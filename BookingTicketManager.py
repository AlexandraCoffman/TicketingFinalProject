from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import requests  # Added for communicating with Event Manager

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///booking_management.db'
db = SQLAlchemy(app)

# Database Models
class Booking(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(50), nullable=False)
    event_id = db.Column(db.String(50), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='confirmed')

class Ticket(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = db.Column(db.String(36), db.ForeignKey('booking.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    seat_number = db.Column(db.String(10))
    price = db.Column(db.Float, nullable=False)

# Routes
@app.route('/book_tickets', methods=['POST'])
def book_tickets():
    """Handle ticket booking with seat type validation"""
    data = request.json

    # Validate required fields
    required = ['user_id', 'event_id', 'ticket_type', 'quantity']
    if not all(field in data for field in required):
        return jsonify({"error": "Missing required fields"}), 400

    # Check seat availability with Event Manager
    check_response = requests.post(
        f'http://localhost:5004/events/{data["event_id"]}/check_seats',
        json={'seat_type': data['ticket_type'], 'quantity': data['quantity']}
    )

    if check_response.status_code != 200 or not check_response.json().get('available'):
        return jsonify({"error": "Not enough seats available for this type"}), 400

    # Reserve the seats
    reserve_response = requests.post(
        f'http://localhost:5004/events/{data["event_id"]}/reserve_seats',
        json={'seat_type': data['ticket_type'], 'quantity': data['quantity']}
    )

    if reserve_response.status_code != 200:
        return jsonify({"error": "Failed to reserve seats"}), 400

    # Create booking
    booking = Booking(
        user_id=data['user_id'],
        event_id=data['event_id']
    )
    db.session.add(booking)
    db.session.flush()

    # Create tickets
    for _ in range(data['quantity']):
        ticket = Ticket(
            booking_id=booking.id,
            type=data['ticket_type'],
            price=calculate_price(data['ticket_type']),
            seat_number=generate_seat_number(data['ticket_type'])
        )
        db.session.add(ticket)

    db.session.commit()
    return jsonify({
        "message": "Booking created",
        "booking_id": booking.id,
        "ticket_count": data['quantity']
    }), 201

@app.route('/all_bookings', methods=['GET'])
def all_bookings():
    """Get all bookings with ticket details"""
    bookings = Booking.query.all()
    return jsonify([{
        "booking_id": b.id,
        "user_id": b.user_id,
        "event_id": b.event_id,
        "status": b.status,
        "tickets": [{
            "type": t.type,
            "seat_number": t.seat_number,
            "price": t.price
        } for t in Ticket.query.filter_by(booking_id=b.id).all()]
    } for b in bookings])

@app.route('/cancel_booking/<booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    """Cancel booking and potentially release seats"""
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    # Get all tickets for this booking
    tickets = Ticket.query.filter_by(booking_id=booking_id).all()

    # Count seats by type to release
    seats_to_release = {}
    for ticket in tickets:
        seats_to_release[ticket.type] = seats_to_release.get(ticket.type, 0) + 1

    # Update booking status
    booking.status = 'cancelled'
    db.session.commit()

    # In a real system, we would notify the Event Manager to release the seats
    # This is simplified for the example
    return jsonify({
        "message": "Booking cancelled",
        "refund_eligible": check_refund_eligibility(booking),
        "seats_released": seats_to_release
    })

@app.route('/manage_bookings/<user_id>', methods=['GET'])
def manage_bookings(user_id):
    """Get bookings for a specific user"""
    bookings = Booking.query.filter_by(user_id=user_id).all()
    return jsonify([{
        "booking_id": b.id,
        "event_id": b.event_id,
        "status": b.status,
        "tickets": [{
            "type": t.type,
            "seat_number": t.seat_number,
            "price": t.price
        } for t in Ticket.query.filter_by(booking_id=b.id).all()]
    } for b in bookings])

# Helper functions
def calculate_price(ticket_type):
    """Calculate price based on ticket type"""
    prices = {
        'regular': 10.0,  # €10 for regular seats
        'vip': 20.0,      # €20 for VIP seats
        'disabled': 5.0    # €5 for disabled seats
    }
    return prices.get(ticket_type.lower(), 10.0)

def generate_seat_number(ticket_type):
    """Generate seat number with type prefix"""
    prefix = {
        'regular': 'R',
        'vip': 'V',
        'disabled': 'D'
    }.get(ticket_type.lower(), 'X')
    return f"{prefix}{1 + len(Ticket.query.all())}"

def check_refund_eligibility(booking):
    """Check if booking is eligible for refund"""
    return (datetime.utcnow() - booking.booking_date).days < 10

# Initialize DB
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(port=5003, debug=True)
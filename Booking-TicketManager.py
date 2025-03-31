from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///booking_management.db'
db = SQLAlchemy(app)

# Database Models
class Booking(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(50), nullable=False)  #link to Account Management
    event_id = db.Column(db.String(50), nullable=False)  #link to Concert Management
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='confirmed')  # confirmed/cancelled/refunded

class Ticket(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = db.Column(db.String(36), db.ForeignKey('booking.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    seat_number = db.Column(db.String(10))
    price = db.Column(db.Float, nullable=False)

# Routes (Matching UML exactly)
@app.route('/book_tickets', methods=['POST'])
def book_tickets():
    """Matches UML: 'Book Tickets (type of tickets)'"""
    data = request.json

    # Validate required fields from UML
    required = ['user_id', 'event_id', 'ticket_type', 'quantity']
    if not all(field in data for field in required):
        return jsonify({"error": "Missing required fields"}), 400

    # Create booking
    booking = Booking(
        user_id=data['user_id'],
        event_id=data['event_id']
    )
    db.session.add(booking)

    # Create tickets (handles UML's "type of tickets")
    for _ in range(data['quantity']):
        ticket = Ticket(
            booking_id=booking.id,
            type=data['ticket_type'],
            price=calculate_price(data['ticket_type']),
            seat_number=generate_seat_number()
        )
        db.session.add(ticket)

    db.session.commit()
    return jsonify({
        "message": "Booking created",
        "booking_id": booking.id,
        "ticket_count": data['quantity']
    }), 201

@app.route('/cancel_booking/<booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    """Matches UML: 'Cancel & Refund'"""
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    booking.status = 'cancelled'
    db.session.commit()

    return jsonify({
        "message": "Booking cancelled",
        "refund_eligible": check_refund_eligibility(booking)
    })

@app.route('/manage_bookings/<user_id>', methods=['GET'])
def manage_bookings(user_id):
    """Matches UML: 'Manage Bookings'"""
    bookings = Booking.query.filter_by(user_id=user_id).all()
    return jsonify([{
        "booking_id": b.id,
        "event_id": b.event_id,
        "status": b.status,
        "tickets": [t.type for t in Ticket.query.filter_by(booking_id=b.id).all()]
    } for b in bookings])

@app.route('/book_venue', methods=['POST'])
def book_venue():
    """Matches UML: 'Book Venues'"""
    data = request.json
    return jsonify({"message": "Venue booking created"}), 201

#pricing based on ticket type
def calculate_price(ticket_type):
    prices = {'regular': 50.0, 'vip': 100.0, 'student': 25.0}
    return prices.get(ticket_type, 50.0)

#seat assignment
def generate_seat_number():
    return f"{chr(65 + len(Ticket.query.all()) % 26)}{1 + len(Ticket.query.all()) // 26}"

#can refund within a number of days
def check_refund_eligibility(booking):
    return (datetime.utcnow() - booking.booking_date).days < 10

# Initialize DB
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(port=5003, debug=True)
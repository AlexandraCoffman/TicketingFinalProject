from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
db = SQLAlchemy(app)

# Database Model
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.String(50), nullable=False)
    venue = db.Column(db.String(100), nullable=False)
    # Changed from available_seats to separate seat types
    regular_seats = db.Column(db.Integer, nullable=False, default=0)
    vip_seats = db.Column(db.Integer, nullable=False, default=0)
    disabled_seats = db.Column(db.Integer, nullable=False, default=0)

# Helper function to calculate total available seats
def get_total_available_seats(event):
    return event.regular_seats + event.vip_seats + event.disabled_seats

#routes
@app.route('/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    event = Event.query.get(event_id)
    if event:
        return jsonify({
            'id': event.id,
            'name': event.name,
            'regular_seats': event.regular_seats,
            'vip_seats': event.vip_seats,
            'disabled_seats': event.disabled_seats
        })
    return jsonify({"error": "Event not found"}), 404

@app.route('/events', methods=['GET'])
def view_events():
    events = Event.query.all()
    return jsonify([{
        'id': e.id,
        'name': e.name,
        'date': e.date,
        'venue': e.venue,
        'regular_seats': e.regular_seats,
        'vip_seats': e.vip_seats,
        'disabled_seats': e.disabled_seats,
        'total_seats': e.regular_seats + e.vip_seats + e.disabled_seats
    } for e in events])


@app.route('/create_event', methods=['POST'])
def create_event():
    data = request.json
    required_fields = ['name', 'date', 'venue', 'regular_seats', 'vip_seats', 'disabled_seats']

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    new_event = Event(
        name=data['name'],
        date=data['date'],
        venue=data['venue'],
        regular_seats=int(data['regular_seats']),
        vip_seats=int(data['vip_seats']),
        disabled_seats=int(data['disabled_seats'])
    )

    db.session.add(new_event)
    db.session.commit()
    return jsonify({"message": "Event created successfully"}), 201

@app.route('/cancel_event/<int:event_id>', methods=['POST'])
def cancel_event(event_id):
    """Cancel an event"""
    event = Event.query.get(event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    db.session.delete(event)
    db.session.commit()
    return jsonify({'message': 'Event cancelled successfully'}), 200

@app.route('/events/<int:event_id>/check_seats', methods=['POST'])
def check_seat_availability(event_id):
    """Check if specific seat types are available"""
    event = Event.query.get(event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404

    data = request.json
    seat_type = data.get('seat_type', '').lower()
    quantity = data.get('quantity', 1)

    # Check availability based on seat type
    available = False
    if seat_type == 'regular' and event.regular_seats >= quantity:
        available = True
    elif seat_type == 'vip' and event.vip_seats >= quantity:
        available = True
    elif seat_type == 'disabled' and event.disabled_seats >= quantity:
        available = True

    return jsonify({
        'available': available,
        'seat_type': seat_type,
        'requested_quantity': quantity
    })

@app.route('/events/<int:event_id>/reserve_seats', methods=['POST'])
def reserve_seats(event_id):
    """Reserve seats of a specific type"""
    event = Event.query.get(event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404

    data = request.json
    seat_type = data.get('seat_type', '').lower()
    quantity = data.get('quantity', 1)

    # Update seat count based on type
    if seat_type == 'regular':
        if event.regular_seats < quantity:
            return jsonify({'error': 'Not enough regular seats available'}), 400
        event.regular_seats -= quantity
    elif seat_type == 'vip':
        if event.vip_seats < quantity:
            return jsonify({'error': 'Not enough VIP seats available'}), 400
        event.vip_seats -= quantity
    elif seat_type == 'disabled':
        if event.disabled_seats < quantity:
            return jsonify({'error': 'Not enough disabled seats available'}), 400
        event.disabled_seats -= quantity
    else:
        return jsonify({'error': 'Invalid seat type'}), 400

    db.session.commit()
    return jsonify({'message': f'Successfully reserved {quantity} {seat_type} seats'})

# Initialize sample data
def init_db():
    with app.app_context():
        db.create_all()
        if not Event.query.first():
            sample_events = [
                Event(name='Summer Concert', description='Outdoor music festival',
                      date='2023-08-15', venue='Central Park',
                      regular_seats=100, vip_seats=40, disabled_seats=10),
                Event(name='Jazz Night', description='Evening of jazz classics',
                      date='2023-08-20', venue='City Hall',
                      regular_seats=60, vip_seats=15, disabled_seats=5)
            ]
            db.session.add_all(sample_events)
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(port=5004, debug=True)
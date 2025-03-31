from flask import Flask, jsonify
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
    available_seats = db.Column(db.Integer, nullable=False)

#routes
@app.route('/events', methods=['GET'])
def view_events():
    """Matches UML: 'Browsing -> Views Available Seats'"""
    events = Event.query.all()
    return jsonify([{
        'id': e.id,
        'name': e.name,
        'date': e.date,
        'venue': e.venue,
        'available_seats': e.available_seats
    } for e in events])

@app.route('/events/<int:event_id>/seats', methods=['GET'])
def view_available_seats(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404

    return jsonify({
        'event_id': event.id,
        'event_name': event.name,
        'available_seats': event.available_seats,
        'seat_map': generate_seat_map(event.available_seats)
    })

def generate_seat_map(total_seats):
    rows = min(10, (total_seats // 20) + 1)
    seats_per_row = (total_seats // rows) + 1
    return {
        'total_seats': total_seats,
        'layout': f'{rows}x{seats_per_row}',
        'available': [f"{chr(65+i)}{j+1}" for i in range(rows) for j in range(seats_per_row)][:total_seats]
    }

# Initialize sample data
def init_db():
    with app.app_context():
        db.create_all()
        if not Event.query.first():
            sample_events = [
                Event(name='Summer Concert', description='Outdoor music festival',
                      date='2023-08-15', venue='Central Park', available_seats=150),
                Event(name='Jazz Night', description='Evening of jazz classics',
                      date='2023-08-20', venue='City Hall', available_seats=80)
            ]
            db.session.add_all(sample_events)
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(port=5004, debug=True)
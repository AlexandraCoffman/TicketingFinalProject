from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///customer_requests.db'
db = SQLAlchemy(app)

# Database Model
class CustomerRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)
    request_type = db.Column(db.String(50), nullable=False)  # refund, exchange, complaint, etc.
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='open')  # open/in-progress/resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

#routes
@app.route('/requests', methods=['POST'])
def create_request():
    data = request.json
    required_fields = ['user_id', 'request_type', 'description']

    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    new_request = CustomerRequest(
        user_id=data['user_id'],
        request_type=data['request_type'],
        description=data['description']
    )

    db.session.add(new_request)
    db.session.commit()

    return jsonify({
        'message': 'Request submitted successfully',
        'request_id': new_request.id,
        'status': new_request.status
    }), 201

@app.route('/requests/<int:request_id>', methods=['PUT'])
def update_request(request_id):
    request_data = CustomerRequest.query.get(request_id)
    if not request_data:
        return jsonify({'error': 'Request not found'}), 404

    if 'status' in request.json:
        request_data.status = request.json['status']
        db.session.commit()

    return jsonify({
        'request_id': request_data.id,
        'new_status': request_data.status
    })

@app.route('/requests/user/<user_id>', methods=['GET'])
def get_user_requests(user_id):
    """Get all requests for a user"""
    requests = CustomerRequest.query.filter_by(user_id=user_id).all()
    return jsonify([{
        'id': r.id,
        'type': r.request_type,
        'status': r.status,
        'created_at': r.created_at.isoformat()
    } for r in requests])

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    init_db()
    app.run(port=5005, debug=True)
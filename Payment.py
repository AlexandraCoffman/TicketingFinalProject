from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payments.db'
db = SQLAlchemy(app)

# Transactions
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)
    event_id = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Completed')  # or Refunded
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Refund Request
class RefundRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False)
    user_id = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='Pending')  #Pending / Approved / Rejected
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/pay', methods=['POST'])
def process_payment():
    data = request.json
    user_id = data.get('user_id')
    event_id = data.get('event_id')
    amount = data.get('amount')

    #integrate with event manager

    transaction = Transaction(user_id=user_id, event_id=event_id, amount=amount)
    db.session.add(transaction)
    db.session.commit()

    return jsonify({"message": "Payment Successful", "transaction_id": transaction.id}), 201

@app.route('/request_refund', methods=['POST'])
def request_refund():
    data = request.json
    transaction_id = data.get('transaction_id')
    user_id = data.get('user_id')

    transaction = Transaction.query.get(transaction_id)
    if not transaction or transaction.user_id != user_id:
        return jsonify({"error": "Invalid transaction"}), 400

    refund_request = RefundRequest(transaction_id=transaction_id, user_id=user_id)
    db.session.add(refund_request)
    db.session.commit()

    return jsonify({"message": "Refund request submitted, awaiting approval."}), 201

@app.route('/approve_refund', methods=['POST'])
def approve_refund():
    data = request.json
    refund_id = data.get('refund_id')

    refund_request = RefundRequest.query.get(refund_id)
    if not refund_request or refund_request.status != 'Pending':
        return jsonify({"error": "Invalid or already processed request"}), 400

    refund_request.status = 'Approved'
    transaction = Transaction.query.get(refund_request.transaction_id)
    transaction.status = 'Refunded'
    db.session.commit()

    return jsonify({"message": "Refund approved successfully."}), 200

@app.route('/transactions', methods=['GET'])
def list_transactions():
    transactions = Transaction.query.all()
    return jsonify([{ "id": t.id, "user_id": t.user_id, "event_id": t.event_id, "amount": t.amount, "status": t.status } for t in transactions])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

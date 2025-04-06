from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import csv
import requests
import os
import stripe

# Initalize the flask, csv file, and login manager
app = Flask(__name__)
app.config['SECRET_KEY'] = 'key' # Allows for the login manager to work and clear cookies so user is logged out upon inital load of the website
csv_file = 'database.csv'
# Stripe API key for payment processing
# I shouldn't be using the actual key here, but for this example, I will
stripe.api_key = "sk_test_51RAs3pBSWTGa5skxDOzMJBOlcKlCzxh6V6DVTHqfpXSYv17pscDq3wfTqW5g4TwGS8PP47AMYo8bPFeMU8mczkZB00imnLp67O"
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@app.route('/')
def index():
    events = []
    try:
        response = requests.get('http://localhost:5004/events', timeout=2)
        if response.status_code == 200:
            events = response.json()
    except requests.exceptions.RequestException:
        flash("Could not load events. Please try again later.", "danger")

    return render_template('index.html', user=current_user, events=events)
# User class with id (class), username, and password
class User(UserMixin):
    def __init__(self, user_class, username, password):
        self.id = username
        self.username = username
        self.password = password
        self.user_class = user_class
# Needed for Flask-Login to work
@login_manager.user_loader
def load_user(user_id):
    users = read_csv()
    for user in users:
        if user.id == user_id:
            return user
    return None
# Function to read users from the CSV file
def read_csv():
    user_credentials = []
    with open(csv_file, newline='') as file:
        reader = csv.reader(file)
        # Skip the first line with the username, password, and user class sections
        next(reader, None)
        for line in reader:
            if len(line) == 3: # Confirm there's three columns in the CSV file
                user_credentials.append(User(line[2], line[0], line[1]))
    return user_credentials

# Function to write new users to the CSV file
def write_csv(username, password, user_class=1):
    with open(csv_file, 'a', newline='\n') as file: # Create a newline in csvfile format for new users
        write = csv.writer(file)
        write.writerow([username, password, user_class])
# Function to login a new user using the CSV file
@app.route('/login', methods=['GET', 'POST'])
def login():
    # User wants to submit the login form
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Read through the CSV file to check if the user exists
        users = read_csv()
        for user in users:
            if user.username == username and user.password == password:
                login_user(user) # If they do, log them in
                return redirect(url_for('profile'))
        # Otherwise, try again
        flash("Invalid username or password. Please try again.", "danger")

    return render_template('login.html')
# Function that registers a new user to the CSV file
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = read_csv()
        # Check if there's anyother user with the same username
        if any(user.username == username for user in users):
            return 'User already exists, please input a different username', 400
        # When registering a new user, the user class is set to 1 = Customer
        write_csv(username, password, 1)
        return redirect(url_for('login'))

    return render_template('register.html')
# Function to logout the user
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Function that display the user profile of a specific user and their functionalities
@app.route('/profile')
@login_required
def profile():
    user_id = current_user.username;
    user_type = current_user.user_class;
    bookings = []
    support_requests = []
    events = [] 
    if user_type == '1': # Customer Profile Page
        # Get the bookings made by the user
        response = requests.get(f"http://localhost:5003/manage_bookings/{user_id}")
        bookings_data = response.json()
        booking_made = []
        # Get the events from the event manager
        events = requests.get('http://localhost:5004/events').json()

        for booking in bookings_data:
            event_name = next((e['name'] for e in events if str(e['id']) == str(booking['event_id'])), None)
            ticket_summary = {}
            seat_numbers = []

            for ticket_type in booking['tickets']:
                ticket_summary[ticket_type] = ticket_summary.get(ticket_type, 0) + 1
            # Create the booking made list
            booking_made.append({"booking_id": booking["booking_id"],"event_id": booking["event_id"], "event_name": event_name, "status": booking["status"], "ticket_summary": ticket_summary,})
        return render_template('user_profile.html', user=current_user, user_type=current_user.user_class, bookings=booking_made)
    elif user_type == '2': # Operator Profile Page
        return render_template('user_profile.html', user=current_user, user_type=current_user.user_class)
    elif user_type == '3': # Organizer Profile Page
        return render_template('user_profile.html', user=current_user, user_type=current_user.user_class) 
# Function that handles Stripe Payment process and displays whether payment was sucessesful or not
@app.route('/pay', methods=['GET', 'POST'])
@login_required
def pay():
    success = request.args.get('success')
    cancel = request.args.get('cancel')
    event_id = request.args.get('event_id')
    event_name = ""
    # Grab the event name from the event ID
    response = requests.get('http://localhost:5004/events')
    # Check if the response is successful
    for event in response.json():
        if str(event.get('id')) == str(event_id):
            event_name = event.get('name')
            break

    # Create the Stripe Session Based on the Information Passed
    if request.method == 'POST':
        # TO HANDLE SEAT SELECTION AND TYPES OF SEATING: EDIT THIS LOGIC
        # Moved logic into POST method for displaying seat type for user profile display
        selected_seat_type = request.form.get('seat_type', 'Regular')
        selected_seat_number = request.form.get('seat_number', 'N/A')

        session['seat_type'] = selected_seat_type
        session['seat_number'] = selected_seat_number
        session['event_id'] = event_id
        # The price is handled in cents for Stripe, i.e. 1000 = 10.00 EUROS
        price_cents = 1000
        if selected_seat_type == "VIP":
            price_cents = 2000
        elif selected_seat_type == "Disabled":
            price_cents = 800
        # Create the Stripe Checkout Session
        stripe_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            # Use Card Number 4242 4242 4242 4242 for testing
            line_items=[{'price_data': {'currency': 'eur', 'product_data': {'name': f'{selected_seat_type} Seat for {event_name}','metadata': {'event_id': event_id,'seat_type': selected_seat_type,'seat_number': selected_seat_number}},'unit_amount': price_cents,},'quantity': 1,}],
            mode='payment',
            # Handle the success and cancel responses from Stripe, Jinja HTML will display the result
            success_url=url_for('pay', _external=True, success='true', event_id=event_id),
            cancel_url=url_for('pay', _external=True, cancel='true', event_id=event_id),
        )
        return redirect(stripe_session.url, code=303)
    # If the payment was successful, we will process the booking
    if success and session.get('event_id'):
        event_id = session.pop('event_id', None)
        selected_seat_type = session.pop('seat_type', None)
        selected_seat_number = session.pop('seat_number', 'N/A')

        booking_payload = {"user_id": current_user.username, "event_id": event_id, "ticket_type": selected_seat_type.lower(), "quantity": 1}

        requests.post("http://localhost:5003/book_tickets", json=booking_payload)
        # Redirect to profile after booking
        return redirect(url_for('profile'))
    # Properly render the response of the payment
    return render_template('pay.html', success=success, cancel=cancel, event_id=event_id, event_name=event_name)
# Function used to call from BookingEventManager to cancel a booking
@app.route('/cancel_booking/<booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    requests.post(f'http://localhost:5003/cancel_booking/{booking_id}')
    return redirect(url_for('profile'))

if __name__ == '__main__':
    app.run(debug=True)

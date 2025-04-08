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
            # Transformez les données pour inclure toutes les informations de sièges
            for event in events:
                event['total_seats'] = event.get('regular_seats', 0) + event.get('vip_seats', 0) + event.get('disabled_seats', 0)
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
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = current_user.username;
    user_type = current_user.user_class;
    support_requests = []
    events = [] 
    if user_type == '1': # Customer Profile Page
        # Get the bookings made by the user
        response = requests.get(f"http://localhost:5003/manage_bookings/{user_id}")
        bookings_data = response.json()
        booking_made = []
        # Get the events from the event manager
        events = requests.get('http://localhost:5004/events').json()
        # Generate the support requests on the customers profile page
        support_requests = requests.get(f"http://localhost:5005/requests/user/{user_id}").json()
        for booking in bookings_data:
            event_name = next((e['name'] for e in events if str(e['id']) == str(booking['event_id'])), None)
            ticket_summary = {}
            seat_numbers = []

            for ticket in booking['tickets']:
                ticket_type = ticket['type']
                ticket_summary[ticket_type] = ticket_summary.get(ticket_type, 0) + 1

            # Create the booking made list
            booking_made.append({"booking_id": booking["booking_id"],"event_id": booking["event_id"], "event_name": event_name, "status": booking["status"], "ticket_summary": ticket_summary,})
        return render_template('user_profile.html', user=current_user, user_type=current_user.user_class, bookings=booking_made, support_requests=support_requests)
    elif user_type == '2':  # Operator Profile Page
        response = requests.get('http://localhost:5004/events')
        organizer_events = response.json()
        # Grab all the current bookings
        all_bookings_raw = requests.get("http://localhost:5003/all_bookings").json()
        all_booking_made = []
        # Then get the events from the event manager
        for booking in all_bookings_raw:
            event_name = next((e['name'] for e in organizer_events if str(e['id']) == str(booking['event_id'])), None)
            ticket_summary = {}
            for ticket in booking['tickets']:
                ticket_type = ticket['type']
                ticket_summary[ticket_type] = ticket_summary.get(ticket_type, 0) + 1

            all_booking_made.append({"booking_id": booking["booking_id"],"user_id": booking["user_id"],"event_id": booking["event_id"],"event_name": event_name,"status": booking["status"],"ticket_summary": ticket_summary})
        # Create an event as a organizer
        if request.method == 'POST':
            name = request.form['name']
            date = request.form['date']
            venue = request.form['venue']
            seats = request.form['seats']
            event_payload = {"name": name,"date": date,"venue": venue,"available_seats": int(seats)}
            requests.post("http://localhost:5004/create_event", json=event_payload)
        # Grab all the support requests for the operator profile page
        support_requests = []
        support_requests = requests.get("http://localhost:5005/requests").json()
        return render_template('user_profile.html', user=current_user, user_type=user_type, organizer_events=organizer_events, all_bookings=all_booking_made, support_requests=support_requests)
    elif user_type == '3':
        response = requests.get('http://localhost:5004/events')
        organizer_events = response.json()
        # Generate the support requests on the organizers profile page
        support_requests = []
        support_requests = requests.get(f"http://localhost:5005/requests/user/{user_id}").json()
        if request.method == 'POST':
            name = request.form['name']
            date = request.form['date']
            venue = request.form['venue']
            seats = request.form['seats']

            event_payload = {"name": name,"date": date,"venue": venue,"available_seats": int(seats)}

            response = requests.post("http://localhost:5004/create_event", json=event_payload)
        return render_template('user_profile.html', user=current_user, user_type=user_type,organizer_events=organizer_events, support_requests=support_requests)
    return render_template('user_profile.html', user=current_user, user_type=user_type, organizer_events=organizer_events)
# Function that handles Stripe Payment process and displays whether payment was sucessesful or not
@app.route('/pay', methods=['GET', 'POST'])
@login_required
def pay():
    """Handle ticket booking and payment processing"""
    event_id = request.args.get('event_id')
    success = request.args.get('success')
    cancel = request.args.get('cancel')

    # Get event details
    try:
        event_response = requests.get(f'http://localhost:5004/events/{event_id}')
        if event_response.status_code != 200:
            flash("Event not found", "danger")
            return redirect(url_for('index'))
        event = event_response.json()
    except requests.exceptions.RequestException:
        flash("Service unavailable", "danger")
        return redirect(url_for('index'))

    event_name = event.get('name', 'Unknown Event')
    seat_availability = {
        'regular': event.get('regular_seats', 0),
        'vip': event.get('vip_seats', 0),
        'disabled': event.get('disabled_seats', 0)
    }

    # Handle payment success
    if success and session.get('event_id'):
        return handle_payment_success(event_name)

    # Handle payment cancellation
    if cancel:
        return render_template('pay.html',
                               cancel=True,
                               event_id=event_id,
                               event_name=event_name)

    # Process booking form
    if request.method == 'POST':
        seat_type = request.form.get('seat_type')
        quantity = int(request.form.get('quantity', 1))

        # Validate seat availability
        available_seats = seat_availability.get(seat_type.lower(), 0)
        if quantity > available_seats:
            flash(f"Only {available_seats} {seat_type} seats available", "warning")
            return redirect(url_for('pay', event_id=event_id))

        # Create Stripe session
        return create_stripe_session(event_id, event_name, seat_type, quantity)

    # Show booking form
    max_available = max(seat_availability.values())
    return render_template('pay.html',
                           event_id=event_id,
                           event_name=event_name,
                           seat_availability=seat_availability,
                           max_available=max_available)

def handle_payment_success(event_name):
    """Finalize booking after successful payment"""
    try:
        booking_data = {
            "user_id": current_user.username,
            "event_id": session.pop('event_id'),
            "ticket_type": session.pop('seat_type').lower(),
            "quantity": session.pop('quantity')
        }
        requests.post("http://localhost:5003/book_tickets", json=booking_data)
        flash("Booking confirmed!", "success")
    except Exception as e:
        flash(f"Booking failed: {str(e)}", "danger")

    return render_template('pay.html',
                           success=True,
                           event_name=event_name)

def create_stripe_session(event_id, event_name, seat_type, quantity):
    """Initialize Stripe payment session"""
    try:
        # Calculate price based on seat type
        price_map = {'Regular': 1000, 'VIP': 2000, 'Disabled': 500}
        unit_price = price_map.get(seat_type, 1000)

        # Store booking info in session
        session.update({
            'event_id': event_id,
            'seat_type': seat_type,
            'quantity': quantity
        })

        # Create Stripe Checkout session
        stripe_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': f'{seat_type} Ticket for {event_name}'
                    },
                    'unit_amount': unit_price,
                },
                'quantity': quantity,
            }],
            mode='payment',
            success_url=url_for('pay', _external=True, success='true', event_id=event_id),
            cancel_url=url_for('pay', _external=True, cancel='true', event_id=event_id),
        )
        return redirect(stripe_session.url, code=303)

    except Exception as e:
        flash(f"Payment error: {str(e)}", "danger")
        return redirect(url_for('pay', event_id=event_id))
# Function used to call from BookingEventManager to cancel a booking
@app.route('/cancel_booking/<booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    requests.post(f'http://localhost:5003/cancel_booking/{booking_id}')
    return redirect(url_for('profile'))
# Function that is used for operators & organizers to create events
@app.route('/create_event', methods=['POST'])
@login_required
def create_event():
    if current_user.user_class not in ['2', '3']:  # Only operators and organizers
        flash("You don't have permission to create events", "danger")
        return redirect(url_for('profile'))

    event_payload = {
        "name": request.form['name'],
        "date": request.form['date'],
        "venue": request.form['venue'],
        "regular_seats": request.form['regular_seats'],
        "vip_seats": request.form['vip_seats'],
        "disabled_seats": request.form['disabled_seats']
    }
    requests.post("http://localhost:5004/create_event", json=event_payload)
    return redirect(url_for('profile'))
# Function that is used for operators & organizers to cancel events
@app.route('/cancel_event/<event_id>', methods=['POST'])
@login_required
def cancel_event(event_id):
    requests.post(f'http://localhost:5004/cancel_event/{event_id}')
    return redirect(url_for('profile'))
# Function for operator to cancel user bookings
@app.route('/cancel_user_booking/<booking_id>', methods=['POST'])
@login_required
def cancel_user_booking(booking_id):
    requests.post(f'http://localhost:5003/cancel_booking/{booking_id}')
    return redirect(url_for('profile'))
# Function that handles customer and organizer support requests
@app.route('/submit_request', methods=['POST'])
@login_required
def submit_request():
    user_id = current_user.username
    request_type = request.form['request_type']
    description = request.form['description']
    request_info = {"user_id": user_id,"request_type": request_type,"description": description}
    requests.post("http://localhost:5005/requests", json=request_info)
    return redirect(url_for('profile'))
# Function the operator uses to resolve a users request
@app.route('/resolve_request/<int:request_id>', methods=['POST'])
@login_required
def resolve_request(request_id):
    requests.put(f"http://localhost:5005/requests/{request_id}",json={"status": "resolved"})
    return redirect(url_for('profile'))

if __name__ == '__main__':
    app.run(debug=True)

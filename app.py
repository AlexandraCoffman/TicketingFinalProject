from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import csv
import requests
import os

# Initalize the flask, csv file, and login manager
app = Flask(__name__)
app.config['SECRET_KEY'] = 'key' # Allows for the login manager to work and clear cookies so user is logged out upon inital load of the website
csv_file = 'database.csv'
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
        return render_template('user_profile.html', user=current_user, user_type=current_user.user_class)
    elif user_type == '2': # Operator Profile Page
        return render_template('user_profile.html', user=current_user, user_type=current_user.user_class)
    elif user_type == '3': # Organizer Profile Page
        return render_template('user_profile.html', user=current_user, user_type=current_user.user_class) 

if __name__ == '__main__':
    app.run(debug=True)

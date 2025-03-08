from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import csv

# Initalize the flask, csv file, and login manager
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key' # Allows for the login manager to work
csv_file = 'database.csv'
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@app.route('/')
def index():
    return render_template('index.html', user=current_user)

# User class with id (class), username, and password
class User(UserMixin):
    def __init__(self, user_id, username, password):
        self.id = user_id
        self.username = username
        self.password = password
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
                return redirect(url_for('index'))
        # Otherwise, try again
        return "Invalid credentials. Please try again.", 401

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

if __name__ == '__main__':
    app.run(debug=True)

# TicketingFinalProject

## Set Up Environment - macOS/Linux
First, you'll need to install and activate your environment with: . .venv/bin/activate'
Next, install Flask with 'pip install Flask', though you may need to update your version with 'pip install --upgrade pip'
Then install 'pip install Flask-Login', we'll be using Flask's built-in feature for our user authentication process.
Use 'pip install Stripe' for the payment method
Now open multiple terminals to run 'flask run' for app.py, 'python Browsing.py', 'python BookingTicketManager.py', and 'python Events.py'
Now you can open the website in port http://127.0.0.1:5000

## Current Workflow
This project implements a basic user authentication system where users can register, log in, and log out. By default, any new account is given a UserClass of 1, which represents a Customer. Organizer (2) and Operator (3) roles are assigned by editing the database.csv file manually. Once logged in, users are taken to a profile page that updates dynamically based on their role, using Jinja templates.

Customers can view and cancel their bookings, as well as submit support requests for things like refunds, exchanges, complaints, or general questions. Organizers have similar access but can also create events and manage seat allocations for Regular, VIP, and Disabled seating. Operators have the most permissions—they can see all bookings and events on the platform and manage support requests submitted by both customers and organizers. When an operator resolves a request, the change is reflected across the system so everyone stays up to date.

The main page displays each available concert with information on the name, date, venue, seating by type, and only allows users with accounts to book. Additionally, there are button hyperlinks to the login or registration page; from either one, the user can navigate to login or registration at any point during this phase. When a logged-in customer books a ticket, they'll be taken to the booking page of that concert, where they'll book the number of tickets and type (VIP, regular, disabled). They'll reroute to a Stripe payment page where they'll be asked to pay by inserting their fake credit card number of 4242 4242 4242 4242, random CSV/Dates, and their name, phone, and email. After that, the user will receive a confirmation page of successful or unsuccessful attempts and will be given the option to view their booking or go back home. At this point, the user can view their bookings via their profile page, and they're done! Available seating is also updated after a booking occurs.



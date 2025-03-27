#Concert Management Subsystem


#Add & Manage Concerts
class Concert:
    def __init__(self, concert_id, artist_name, date, time, ticket_price, seat_num):
        self.concert_id = concert_id
        self.artist_name = artist_name
        self.date = date
        self.time = time
        self.ticket_price = ticket_price
        self.seats_available = seat_num

    def ticket_update(self, tickets_sold):

        if tickets_sold <= self.seats_available:
            self.seats_available =- tickets_sold
            print("Number of available seats: ", self.seats_available)

        else:
            print("There are no seats available")

    def set_ticketprice (self, set_price):
        self.ticket_price = set_price
        print("Ticket price is: ", self.ticket_price)

    def to_databse (self):
        return {
            "concert_id": self.concert_id,
            "artist_name": self.artist_name,
            "date": self.date,
            "time": self.time,
            "ticket_price": self.ticket_price,
            "seat_num": self.seat_num,
            "seats_available": self.seats_available,
        }


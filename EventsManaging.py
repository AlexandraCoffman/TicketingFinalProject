import csv
from datetime import datetime
import os

class Event:
    def __init__(self, event_id, name, description, date, max_tickets, ticket_price):
        self.event_id = event_id
        self.name = name
        self.description = description
        self.date = date
        self.max_tickets = max_tickets
        self.ticket_price = ticket_price
        self.sold_tickets = 0

    def available_tickets(self):
        return self.max_tickets - self.sold_tickets

    def sell_ticket(self, quantity=1):
        if self.sold_tickets + quantity <= self.max_tickets:
            self.sold_tickets += quantity
            return True
        return False

    def to_dict(self):
        return {
            'event_id': self.event_id,
            'name': self.name,
            'description': self.description,
            'date': self.date,
            'max_tickets': self.max_tickets,
            'ticket_price': self.ticket_price,
            'sold_tickets': self.sold_tickets
        }

class EventManager:
    def __init__(self, filename='events.csv'):
        self.filename = filename
        self.events = {}
        self.load_events()

    def load_events(self):
        if not os.path.exists(self.filename):
            return

        with open(self.filename, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                event = Event(
                    event_id=row['event_id'],
                    name=row['name'],
                    description=row['description'],
                    date=row['date'],
                    max_tickets=int(row['max_tickets']),
                    ticket_price=float(row['ticket_price'])
                )
                event.sold_tickets = int(row['sold_tickets'])
                self.events[event.event_id] = event

    def save_events(self):
        with open(self.filename, mode='w', newline='') as file:
            fieldnames = ['event_id', 'name', 'description', 'date',
                          'max_tickets', 'ticket_price', 'sold_tickets']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for event in self.events.values():
                writer.writerow(event.to_dict())

    def create_event(self, name, description, date, max_tickets, ticket_price):
        event_id = f"evt_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        event = Event(event_id, name, description, date, max_tickets, ticket_price)
        self.events[event.event_id] = event
        self.save_events()
        return event

    def get_event(self, event_id):
        return self.events.get(event_id)

    def list_events(self):
        return list(self.events.values())

    def purchase_tickets(self, event_id, quantity):
        event = self.get_event(event_id)
        if event and event.sell_ticket(quantity):
            self.save_events()
            return True
        return False

def main():
    manager = EventManager()
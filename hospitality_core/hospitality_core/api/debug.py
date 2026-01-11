
import frappe
from frappe.utils import nowdate

def check_data():
    rooms = frappe.db.count('Hotel Room')
    reservations_today = frappe.db.count('Hotel Reservation', {'arrival_date': nowdate()})
    statuses = list(set([r.status for r in frappe.db.get_all('Hotel Reservation', {'arrival_date': nowdate()}, ['status'])]))
    
    print(f"DEBUG_START")
    print(f"Rooms: {rooms}")
    print(f"Reservations Today: {reservations_today}")
    print(f"Statuses: {statuses}")
    print(f"DEBUG_END")

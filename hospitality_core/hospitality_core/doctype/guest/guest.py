import frappe
from frappe import _
from frappe.model.document import Document

class Guest(Document):
    def validate(self):
        if not self.customer:
            customer = frappe.new_doc("Customer")
            customer.customer_name = self.full_name
            customer.customer_type = "Individual"
            customer.flags.ignore_permissions = True
            customer.insert()
            self.customer = customer.name

@frappe.whitelist()
def get_guest_stats(guest):
    # 1. Stays & Last Room
    stays = frappe.get_all("Hotel Reservation", 
        filters={"guest": guest, "status": "Checked Out"},
        fields=["name", "room"],
        order_by="departure_date desc",
        limit=1
    )
    
    total_stays = frappe.db.count("Hotel Reservation", {"guest": guest, "status": "Checked Out"})
    last_room = stays[0].room if stays else None

    # 2. Financials (Total Spend from Closed Folios)
    financials = frappe.db.sql("""
        SELECT SUM(total_charges) as total
        FROM `tabGuest Folio`
        WHERE guest = %s AND status = 'Closed'
    """, (guest,), as_dict=True)[0]
    
    total_spend = financials.total or 0.0
    avg_rate = (total_spend / total_stays) if total_stays else 0

    return {
        "total_stays": total_stays,
        "last_room": last_room,
        "total_spend": total_spend,
        "avg_rate": avg_rate
    }
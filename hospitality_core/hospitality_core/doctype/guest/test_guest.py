import frappe
from frappe.tests.utils import FrappeTestCase

class TestGuest(FrappeTestCase):
    def test_guest_creation_creates_customer(self):
        # Create a guest without a customer
        guest_name = "Test Guest Auto Customer"
        
        # Ensure cleanup
        if frappe.db.exists("Guest", {"full_name": guest_name}):
            frappe.delete_doc("Guest", frappe.db.get_value("Guest", {"full_name": guest_name}))
        if frappe.db.exists("Customer", {"customer_name": guest_name}):
            frappe.delete_doc("Customer", {"customer_name": guest_name})

        guest = frappe.get_doc({
            "doctype": "Guest",
            "full_name": guest_name,
            "guest_type": "Regular",
            "email_id": "test_guest@example.com",
            "mobile_no": "1234567890"
        })
        guest.insert()

        # Reload guest to check if customer link is set
        guest.reload()
        self.assertTrue(guest.customer, "Customer link should be set on Guest")

        # Verify Customer details
        customer = frappe.get_doc("Customer", guest.customer)
        self.assertEqual(customer.customer_name, guest_name)
        self.assertEqual(customer.customer_type, "Individual")

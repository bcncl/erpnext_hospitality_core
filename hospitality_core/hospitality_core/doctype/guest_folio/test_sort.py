import frappe
from frappe.utils import nowdate, add_days

def execute():
    # 1. Create a dummy Guest and Folio
    if not frappe.db.exists("Guest", "Sort Test Guest"):
        g = frappe.new_doc("Guest")
        g.full_name = "Sort Test Guest"
        g.guest_type = "Regular"
        g.insert()
    
    guest = "Sort Test Guest"
    
    # Create Folio
    folio = frappe.new_doc("Guest Folio")
    folio.guest = guest
    folio.status = "Open"
    folio.save()
    folio.reload()
    
    print(f"Created Folio: {folio.name}")
    
    # 2. Add Transactions out of order
    # Add 'Today' first
    folio.append("transactions", {
        "item": "ROOM-RENT",
        "description": "Charge Today",
        "amount": 100,
        "posting_date": nowdate()
    })
    
    # Add 'Yesterday' second
    folio.append("transactions", {
        "item": "ROOM-RENT",
        "description": "Charge Yesterday",
        "amount": 100,
        "posting_date": add_days(nowdate(), -1) # Before Today
    })
    
    # Save (Should Trigger Sort)
    folio.save()
    
    # 3. Verify Order
    folio.reload()
    
    txns = folio.transactions
    print(f"Row 1 Date: {txns[0].posting_date}")
    print(f"Row 2 Date: {txns[1].posting_date}")
    
    if txns[0].posting_date < txns[1].posting_date:
        print("SUCCESS: Transactions are sorted chronologically.")
    else:
        print("FAILURE: Transactions are NOT sorted.")
        
    # Cleanup
    # Delete transactions first to avoid on_trash error
    folio.transactions = []
    folio.save()
    frappe.delete_doc("Guest Folio", folio.name)

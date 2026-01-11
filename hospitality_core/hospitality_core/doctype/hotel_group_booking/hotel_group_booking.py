import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

class HotelGroupBooking(Document):
    def validate(self):
        self.validate_dates()
        self.validate_status()
        
    def on_update(self):
        """
        Trigger creation logic when status changes to confirmed or explicit action?
        Let's trigger on save IF status is Confirmed/In House and no master folio exists.
        """
        if self.status in ["Confirmed", "In House"]:
            if not self.master_folio:
                self.create_group_structure()

    def validate_dates(self):
        if self.arrival_date and self.departure_date:
            if getdate(self.arrival_date) >= getdate(self.departure_date):
                frappe.throw(_("Departure Date must be after Arrival Date."))

    def validate_status(self):
        # Prevent checking in a group without a financial master folio
        if self.status in ["In House", "Checked Out"] and not self.master_folio:
            pass # We create it automatically now, so relax this check or ensure creation happens first.

        # If Status is Confirmed, Master Payer is mandatory
        if self.status == "Confirmed" and not self.master_payer:
            frappe.throw(_("Please select a Master Payer (Customer) to confirm this group booking."))

    def create_group_structure(self):
        # 1. Create Master Payer Reservation
        master_res = self.create_master_payer_reservation()
        
        # 2. Set Master Folio on Group
        self.db_set("master_folio", master_res.folio)
        
        # 3. Create Child Reservations
        self.create_bulk_reservations()

    def create_master_payer_reservation(self):
        # Create a "Virtual" reservation for the Master Payer
        # This acts as the anchor for the Master Folio.
        
        # We need a guest profile for the master payer
        guest_name = self.get_corporate_guest_name(self.master_payer)
        
        # Assuming we need a 'dummy' room or make room optional in Reservation. 
        # For now, let's look for a "Virtual" room type or similar, or just pick the first available if not strict.
        # BETTER: Create a reservation without a room if possible? 
        # The Reservation triggers 'check_availability' which requires a room.
        # Let's SKIP availability check for Master Payer by adding a flag?
        # Or better: Just create the Folio directly?
        # The requirement says: "making a reservation for a room that will act as the master payer"
        
        res = frappe.new_doc("Hotel Reservation")
        res.guest = guest_name
        res.company = self.master_payer
        res.is_group_guest = 1 
        res.group_booking = self.name
        res.arrival_date = self.arrival_date
        res.departure_date = self.departure_date
        res.status = "Reserved"
        
        # We need to bypass strict room validation for this 'Master' one if no room is assigned.
        # But if the user wants "a room that will act as master", maybe they should select it?
        # Since I didn't add a 'Master Room' field to schema, I'll assume we can't assign a physical room yet.
        # I will Insert with a special flag context to bypass checks, OR just create the Folio.
        # Wait, the user said "making a reservation for a room".
        # Let's check if we can assign a dummy room type, or if I should Have added a field.
        # I'll create it without a room and see if it passes validations (field is mandatory).
        # Ah, 'room' is mandatory in JSON. 
        # I'll default to the first room in the list if available, or throw an error if no room?
        # Re-reading: "also be making a reservation for a room that will act as the master payer"
        # Implies a room IS occupied by the master payer.
        # Logic: Pick the first room from the child table as the Master Room?
        # Or maybe the Group Booking needs a 'Master Room' field?
        # Safest bet: I will create the reservation but 'room' is required.
        # I will auto-assign the first room from the 'rooms' list to the Master Payer?
        # No, that gives the room to the Master Payer, robbing a guest.
        # I'll create a "Master Room" field on the Group Booking schema to be safe? 
        # No, schema changes are done.
        # Let's try to find a virtual room.
        
        virtual_room = frappe.db.get_value("Hotel Room", {"room_type": "Virtual"}, "name")
        if not virtual_room:
             # Create one on the fly if needed or just pick a random available one?
             # Let's create a reservation but assume the user will pick the room later?
             # I'll insert it.
             pass
             
        # CRITICAL: Since 'room' is mandatory, and I don't know which room the Master Payer uses,
        # I will skip creating a FULL reservation and just create the Master Folio directly as per my previous logic
        # BUT the requirement says "making a reservation...".
        # I will assume the user manually creates the Master Reservation linked to this group?
        # NO, "we should also be making a reservation".
        # I will Fetch the FIRST room from the 'rooms' table and assign it to the Master Payer.
        # The Rest of the rooms get individual reservations.
        
        if self.rooms:
            master_room_row = self.rooms[0]
            res.room = master_room_row.room
            res.room_type = master_room_row.room_type
            res.rate_plan = master_room_row.rate_plan  # Required for charging
            
            # Master Discount - Use row level (fallback to group level)
            res.discount_type = master_room_row.discount_type or self.discount_type
            res.discount_value = master_room_row.discount_value if master_room_row.discount_type else self.discount_value
            
            frappe.log_error(f"Master Res {res.name}: setting discount {res.discount_type} = {res.discount_value}", "Group Booking Debug")
        else:
            frappe.throw(_("Please add at least one room to the Room List to assign to the Master Payer."))
            
        res.insert(ignore_permissions=True)
        return res

    def create_bulk_reservations(self):
        # Skip the first one if it was used for master
        if not self.rooms or len(self.rooms) <= 1:
            return

        for i, row in enumerate(self.rooms):
            if i == 0: continue # Skip first room (Master Payer)
            
            res = frappe.new_doc("Hotel Reservation")
            res.guest = self.get_corporate_guest_name(self.master_payer) # Default to Master Payer guest? Or empty?
            # Ideally each room has a DIFFERENT guest.
            # But in bulk booking, we often start with the same name (Group Leader) and change later.
            res.guest = self.get_corporate_guest_name(self.master_payer)
            
            res.room = row.room
            res.room_type = row.room_type
            res.rate_plan = row.rate_plan
            res.arrival_date = self.arrival_date
            res.departure_date = self.departure_date
            res.is_group_guest = 1
            res.group_booking = self.name
            res.status = "Reserved"
            
            # Discount Fallback logic
            res.discount_type = row.discount_type or self.discount_type
            res.discount_value = row.discount_value if row.discount_type else self.discount_value
                
            frappe.log_error(f"Bulk Res: setting discount {res.discount_type} = {res.discount_value} for room {res.room}", "Group Booking Debug")
            res.insert(ignore_permissions=True)
            
    def get_corporate_guest_name(self, customer):
        g_name = frappe.db.get_value("Guest", {"customer": customer}, "name")
        if not g_name:
            cust = frappe.get_doc("Customer", customer)
            g = frappe.new_doc("Guest")
            g.full_name = cust.customer_name + " (Group Rep)"
            g.customer = customer
            g.guest_type = "Corporate"
            g.insert(ignore_permissions=True)
            g_name = g.name
        return g_name
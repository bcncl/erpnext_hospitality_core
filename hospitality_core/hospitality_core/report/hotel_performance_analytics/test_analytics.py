from hospitality_core.hospitality_core.report.hotel_performance_analytics.hotel_performance_analytics import execute
from frappe.utils import nowdate, add_days

print("Running Hotel Performance Analytics Test...")
try:
    # Use dummy filters
    filters = {
        "from_date": add_days(nowdate(), -3),
        "to_date": nowdate(),
        "hotel_reception": "Test Reception" # Will return 0 data but test query syntax
    }
    
    import frappe
    if frappe.db.exists("Hotel Reception"):
        filters["hotel_reception"] = frappe.db.get_value("Hotel Reception", {}, "name")
        print(f"Using Reception: {filters['hotel_reception']}")
    
    columns, data, message, chart = execute(filters)
    print("Columns:", len(columns))
    print("Data Rows:", len(data))
    if data:
        print("Sample Row:", data[0])
        
    print("Test Complete: Success")
except Exception as e:
    print(f"Test Failed: {e}")
    import traceback
    traceback.print_exc()

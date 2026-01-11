
import frappe
from hospitality_core.hospitality_core.report.daily_sales_consumption.daily_sales_consumption import execute

def verify():
    # Mock filters
    filters = {
        "from_date": "2024-01-01",
        "to_date": "2025-01-01",
        "include_non_revenue": 0
    }
    
    try:
        columns, data = execute(filters)
        if not data:
            print("No data found to verify against, but at least it didn't crash.")
            return

        last_row = data[-1]
        print(f"Last row data: {last_row}")
        
        if last_row.get("guest_name") == "<b>TOTAL</b>":
             print("FAILURE: Total row still present in data!")
        else:
             print("SUCCESS: No total row found in data.")

    except Exception as e:
        print(f"Error during verification: {e}")

if __name__ == "__main__":
    frappe.init(site="site1.local")
    frappe.connect()
    verify()

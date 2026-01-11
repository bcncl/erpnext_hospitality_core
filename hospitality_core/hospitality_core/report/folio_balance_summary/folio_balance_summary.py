import frappe
from frappe import _

def execute(filters=None):
    columns = [
        {"label": _("Ledger Type"), "fieldname": "ledger_type", "fieldtype": "Data", "width": 180},
        {"label": _("Description"), "fieldname": "description", "fieldtype": "Data", "width": 250},
        {"label": _("Count"), "fieldname": "count", "fieldtype": "Int", "width": 80},
        {"label": _("Total Receivable"), "fieldname": "balance", "fieldtype": "Currency", "width": 140},
        {"label": _("Total Liability (Credits)"), "fieldname": "liability", "fieldtype": "Currency", "width": 160}
    ]

    data = []

    # 1. Calculate Guest Ledger (In-House Private Guests)
    guest_stats = frappe.db.sql("""
        SELECT 
            COUNT(name) as cnt, 
            SUM(CASE WHEN outstanding_balance > 0 THEN outstanding_balance ELSE 0 END) as bal,
            SUM(excess_payment) as liability
        FROM `tabGuest Folio`
        WHERE status = 'Open' 
        AND (company IS NULL OR company = '')
    """, as_dict=True)[0]

    data.append({
        "ledger_type": "Guest Ledger",
        "description": "Current In-House Guests (Private Pay)",
        "count": guest_stats.cnt or 0,
        "balance": guest_stats.bal or 0.0,
        "liability": guest_stats.liability or 0.0
    })

    # 2. Calculate City Ledger (Corporate/Direct Bill)
    city_stats = frappe.db.sql("""
        SELECT 
            COUNT(name) as cnt, 
            SUM(CASE WHEN outstanding_balance > 0 THEN outstanding_balance ELSE 0 END) as bal,
            SUM(excess_payment) as liability
        FROM `tabGuest Folio`
        WHERE status = 'Open' 
        AND company IS NOT NULL 
        AND company != ''
    """, as_dict=True)[0]

    data.append({
        "ledger_type": "City Ledger",
        "description": "Corporate Accounts / Direct Bill Masters",
        "count": city_stats.cnt or 0,
        "balance": city_stats.bal or 0.0,
        "liability": city_stats.liability or 0.0
    })

    # 3. Total
    total_bal = (guest_stats.bal or 0) + (city_stats.bal or 0)
    total_lia = (guest_stats.liability or 0) + (city_stats.liability or 0)
    data.append({
        "ledger_type": "<b>TOTAL</b>",
        "description": "",
        "count": (guest_stats.cnt or 0) + (city_stats.cnt or 0),
        "balance": total_bal,
        "liability": total_lia
    })

    chart = {
        "data": {
            "labels": ["Guest Ledger (Rec)", "Guest Ledger (Lia)", "City Ledger (Rec)", "City Ledger (Lia)"],
            "datasets": [
                {
                    "name": "Balance", 
                    "values": [
                        guest_stats.bal or 0, 
                        guest_stats.liability or 0, 
                        city_stats.bal or 0, 
                        city_stats.liability or 0
                    ]
                }
            ]
        },
        "type": "donut",
        "colors": ["#28a745", "#ffc107", "#007bff", "#dc3545"]
    }

    return columns, data, None, chart
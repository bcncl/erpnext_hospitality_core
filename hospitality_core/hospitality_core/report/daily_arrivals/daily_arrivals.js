frappe.query_reports["Daily Arrivals"] = {
    "filters": [
        {
            "fieldname": "date",
            "label": __("Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.now_date(),
            "reqd": 1
        },
        {
            "fieldname": "hotel_reception",
            "label": __("Hotel Reception"),
            "fieldtype": "Link",
            "options": "Hotel Reception"
        }
    ]
};
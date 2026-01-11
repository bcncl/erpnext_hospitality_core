# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"fieldname": "metric",
			"label": _("Metric"),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "value",
			"label": _("Value"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "description",
			"label": _("Description"),
			"fieldtype": "Data",
			"width": 300
		}
	]

def get_data(filters):
	if not filters or not filters.get("date") or not filters.get("hotel_reception"):
		return []

	report_date = filters.get("date")
	reception = filters.get("hotel_reception")

	data = []

	# 1. New Check-ins
	check_ins = frappe.db.count("Hotel Reservation", {
		"arrival_date": report_date,
		"hotel_reception": reception,
		"status": ["in", ["Checked In", "Checked Out"]] # Include those who checked out same day? usually yes for statistics
	})
	
	# Refine Check-in query: Actually status could be 'Checked In' or 'Checked Out' if they left same day, 
	# but primarily we want to know how many ARRIVED this day.
	# Let's trust 'arrival_date' and status != Cancelled/Reserved?
	# "Reserved" implies they haven't arrived yet (no show or future).
	# So status in Checked In, Checked Out.
	
	data.append({
		"metric": "New Check-ins",
		"value": check_ins,
		"description": "Number of guests who arrived and checked in on this date."
	})

	# 2. Retained (Stay-overs)
	# Guests who arrived BEFORE today and depart AFTER today.
	# Status must be 'Checked In'.
	retained = frappe.db.sql("""
		SELECT count(name) FROM `tabHotel Reservation`
		WHERE
			arrival_date < %s
			AND departure_date > %s
			AND hotel_reception = %s
			AND status = 'Checked In'
	""", (report_date, report_date, reception))[0][0]

	data.append({
		"metric": "Retained Guests",
		"value": retained,
		"description": "Guests currently in-house (arrived before today, leaving after today)."
	})

	# 3. Departures (Check-outs)
	top_departures = frappe.db.count("Hotel Reservation", {
		"departure_date": report_date,
		"hotel_reception": reception,
		"status": "Checked Out"
	})

	data.append({
		"metric": "Departures",
		"value": top_departures,
		"description": "Number of guests who checked out on this date."
	})

	# 4. Sales Consumption
	# Sum of Folio Transactions posted on this date, linked to guests in this reception.
	# We need to join Guest Folio to filter by Reception if Folio Transaction doesn't have it (it doesn't).
	# Wait, Folio Transaction does NOT have reception. Guest Folio HAS reception.
	
	sales_consumption = frappe.db.sql("""
		SELECT SUM(ft.amount)
		FROM `tabFolio Transaction` ft
		JOIN `tabGuest Folio` gf ON ft.parent = gf.name
		WHERE
			ft.posting_date = %s
			AND gf.hotel_reception = %s
			AND ft.is_void = 0
            AND gf.docstatus < 2
            AND (ft.reference_doctype != 'Payment Entry' OR ft.reference_doctype IS NULL)
	""", (report_date, reception))[0][0] or 0.0

	data.append({
		"metric": "Sales Consumption",
		"value": frappe.format_value(sales_consumption, currency=frappe.get_cached_value('Company',  frappe.defaults.get_user_default("Company"),  "default_currency")),
		"description": "Total value of services/goods consumed and posted to folios."
	})

	# 5. Payment
	# Sum of Payment Entries for this reception on this date.
	payments = frappe.db.sql("""
		SELECT SUM(paid_amount)
		FROM `tabPayment Entry`
		WHERE
			posting_date = %s
			AND hotel_reception = %s
			AND docstatus = 1
	""", (report_date, reception))[0][0] or 0.0

	data.append({
		"metric": "Total Payments",
		"value": frappe.format_value(payments, currency=frappe.get_cached_value('Company',  frappe.defaults.get_user_default("Company"),  "default_currency")),
		"description": "Total payments collected at this reception."
	})

	# 6. Analytics
	# Occupancy = (Retained + New Check-ins) / Total Rooms in Reception
	total_rooms = frappe.db.count("Hotel Room", {
		"hotel_reception": reception,
		"is_enabled": 1,
		"status": ["!=", "Out of Order"] 
	})

	occupancy_pct = 0.0
	if total_rooms > 0:
		# Occupied = Retained + Check-ins (Assuming check-ins stayed the night, which is typical for EOD report)
		occupied_rooms = retained + check_ins
		occupancy_pct = (occupied_rooms / total_rooms) * 100.0

	data.append({
		"metric": "Occupancy",
		"value": f"{occupancy_pct:.2f}%",
		"description": f"Occupancy Percentage ({retained + check_ins} occupied / {total_rooms} available rooms)."
	})
	
	return data

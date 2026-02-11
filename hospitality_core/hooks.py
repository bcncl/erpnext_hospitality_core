app_name = "hospitality_core"
app_title = "Hospitality Core"
app_publisher = "Gift Braimah"
app_description = "Hotel Management Module"
app_email = "braimahgifted@gmail.com"
app_license = "gpl-2.0"

required_apps = ["frappe/erpnext"]

# Document Events
doc_events = {
    "Guest Folio": {
        "on_update": "hospitality_core.hospitality_core.api.folio.sync_folio_balance"
    },
    "Folio Transaction": {
        "after_save": "hospitality_core.hospitality_core.api.folio.sync_folio_balance",
        "on_trash": "hospitality_core.hospitality_core.api.folio.sync_folio_balance"
    },
    "POS Invoice": {
        "on_submit": "hospitality_core.hospitality_core.api.pos_bridge.process_room_charge",
        "on_cancel": "hospitality_core.hospitality_core.api.pos_bridge.void_room_charge"
    },
    "Payment Entry": {
        "on_submit": "hospitality_core.hospitality_core.api.payment_bridge.process_payment_entry"
    }
}

after_install = "hospitality_core.setup.after_install"

# Scheduled Tasks
# changed daily audit to run at 2 PM (14:00) per requirements
scheduler_events = {
    "cron": {
        "0 14 * * *": [
            "hospitality_core.hospitality_core.api.night_audit.run_daily_audit"
        ]
    }
}

# Fixtures
fixtures = [
    {"dt": "Custom Field", "filters": [["module", "=", "Hospitality Core"]]},
    {"dt": "Property Setter", "filters": [["module", "=", "Hospitality Core"]]}
]

app_name = "nexova_ai"
app_title = "Invoxia AI"
app_publisher = "Invoxia"
app_description = "Privacy-first AI assistant for ERPNext."
app_email = "admin@example.com"
app_license = "MIT"
required_apps = ["erpnext"]

app_include_css = "/assets/nexova_ai/css/nexova_ai.css"

scheduler_events = {
    "hourly": [
        "nexova_ai.assistant.license.sync_license_status",
    ],
    "daily": [
        "nexova_ai.assistant.retention.cleanup_audit_logs",
    ],
}

doc_events = {
    "*": {
        "before_insert": "nexova_ai.assistant.read_only.enforce_write_allowed",
        "before_save": "nexova_ai.assistant.read_only.enforce_write_allowed",
        "before_submit": "nexova_ai.assistant.read_only.enforce_write_allowed",
        "before_cancel": "nexova_ai.assistant.read_only.enforce_write_allowed",
        "on_trash": "nexova_ai.assistant.read_only.enforce_write_allowed",
    },
}

app_name = "nexova_ai"
app_title = "Invoxia AI"
app_publisher = "Invoxia"
app_description = "Privacy-first AI assistant for ERPNext."
app_email = "admin@example.com"
app_license = "MIT"
required_apps = ["erpnext"]

app_include_css = "/assets/nexova_ai/css/nexova_ai.css"

scheduler_events = {
    "daily": [
        "nexova_ai.assistant.retention.cleanup_audit_logs",
    ],
}

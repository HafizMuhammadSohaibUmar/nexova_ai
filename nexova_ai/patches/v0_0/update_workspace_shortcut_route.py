from __future__ import annotations

import json

import frappe


def execute() -> None:
    if not frappe.db.exists("Workspace", "Nexova AI"):
        return

    workspace = frappe.get_doc("Workspace", "Nexova AI")
    shortcuts = [
        {
            "id": "nexova_ai_assistant_shortcut",
            "shortcut_name": "Open Nexova AI",
            "link_to": "nexova-ai-assistant",
            "type": "Page",
            "route": "/app/nexova-ai-assistant",
            "color": "Blue",
            "doc_view": "",
        },
        {
            "id": "nexova_ai_settings_shortcut",
            "shortcut_name": "Nexova AI Settings",
            "link_to": "Nexova AI Settings",
            "type": "DocType",
            "route": "/app/nexova-ai-settings",
            "color": "Grey",
            "doc_view": "",
        },
        {
            "id": "nexova_ai_audit_shortcut",
            "shortcut_name": "Nexova AI Audit Log",
            "link_to": "Nexova AI Audit Log",
            "type": "DocType",
            "route": "/app/nexova-ai-audit-log",
            "color": "Grey",
            "doc_view": "List",
        },
    ]

    workspace.content = json.dumps(
        [{
            "id": "nexova_ai_header",
            "type": "header",
            "data": {
                "text": '<span class="h4">Nexova AI</span>',
                "col": 12,
            },
        }]
        + [
            {
                "id": shortcut["id"],
                "type": "shortcut",
                "data": {
                    "shortcut_name": shortcut["shortcut_name"],
                    "link_to": shortcut["link_to"],
                    "type": shortcut["type"],
                    "route": shortcut["route"],
                    "col": 3,
                },
            }
            for shortcut in shortcuts
        ],
        separators=(",", ":"),
    )

    workspace.set("shortcuts", [])

    for shortcut in shortcuts:
        row = workspace.append("shortcuts", {})
        row.type = shortcut["type"]
        row.label = shortcut["shortcut_name"]
        row.link_to = shortcut["link_to"]
        row.color = shortcut["color"]
        row.doc_view = shortcut["doc_view"]
        row.format = "{}"
        row.stats_filter = "[]"

    workspace.save(ignore_permissions=True)
    frappe.clear_cache()

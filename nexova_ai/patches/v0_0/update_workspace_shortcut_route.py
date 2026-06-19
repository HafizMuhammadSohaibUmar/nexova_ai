from __future__ import annotations

import json

import frappe


def execute() -> None:
    if not frappe.db.exists("Workspace", "Nexova AI"):
        return

    workspace = frappe.get_doc("Workspace", "Nexova AI")
    workspace.content = json.dumps(
        [
            {
                "id": "nexova_ai_header",
                "type": "header",
                "data": {
                    "text": '<span class="h4">Nexova AI</span>',
                    "col": 12,
                },
            },
            {
                "id": "nexova_ai_shortcuts",
                "type": "shortcut",
                "data": {
                    "shortcut_name": "Open Nexova AI",
                    "link_to": "nexova-ai-assistant",
                    "type": "Page",
                    "route": "/app/nexova-ai-assistant",
                    "col": 3,
                },
            },
        ],
        separators=(",", ":"),
    )

    if workspace.shortcuts:
        shortcut = workspace.shortcuts[0]
    else:
        shortcut = workspace.append("shortcuts", {})

    shortcut.type = "Page"
    shortcut.label = "Open Nexova AI"
    shortcut.link_to = "nexova-ai-assistant"
    shortcut.color = "Blue"
    shortcut.format = "{}"
    shortcut.stats_filter = "[]"

    workspace.save(ignore_permissions=True)
    frappe.clear_cache()

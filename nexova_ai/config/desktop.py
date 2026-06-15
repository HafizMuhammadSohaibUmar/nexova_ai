from frappe import _


def get_data():
    return [
        {
            "module_name": "Nexova AI",
            "category": "Modules",
            "label": _("Nexova AI"),
            "color": "blue",
            "icon": "octicon octicon-comment-discussion",
            "type": "module",
            "description": _("AI assistant for ERPNext queries."),
        }
    ]

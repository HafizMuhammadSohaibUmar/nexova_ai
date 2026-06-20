from frappe import _


def get_data():
    return [
        {
            "module_name": "Nexova AI",
            "category": "Modules",
            "label": _("Invoxia AI"),
            "color": "black",
            "icon": "octicon octicon-comment-discussion",
            "type": "module",
            "description": _("Privacy-first AI assistant for ERPNext."),
        }
    ]

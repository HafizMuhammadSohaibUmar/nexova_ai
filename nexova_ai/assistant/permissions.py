from __future__ import annotations

import frappe


def has_required_role(role: str) -> bool:
    return role in set(frappe.get_roles())


def can_read_doctype(doctype: str) -> bool:
    try:
        return bool(frappe.has_permission(doctype=doctype, ptype="read"))
    except Exception:
        try:
            frappe.get_list(doctype, fields=["name"], limit_page_length=1)
            return True
        except Exception:
            return False


def filter_readable_doctypes(doctypes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(doctype for doctype in doctypes if can_read_doctype(doctype))

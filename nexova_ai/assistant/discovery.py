from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import frappe

from nexova_ai.assistant.permissions import can_read_doctype
from nexova_ai.assistant.vocabulary import (
    business_aliases_for_label,
    canonical_text,
    fuzzy_match_score,
)


@dataclass(frozen=True)
class DiscoveredRoute:
    name: str
    label: str
    route: tuple[str, ...]
    category: str
    required_doctype: str | None = None


def find_navigation_routes(question: str, limit: int = 8) -> list[DiscoveredRoute]:
    text = canonical_text(question)
    routes: list[tuple[int, DiscoveredRoute]] = []

    for doctype in _readable_doctypes():
        score = _match_score(text, doctype["label"], doctype["aliases"])
        if score:
            routes.append(
                (
                    score,
                    DiscoveredRoute(
                        name=f"doctype:{doctype['name']}",
                        label=f"{doctype['label']} List",
                        route=("List", doctype["name"]),
                        category="doctype",
                        required_doctype=doctype["name"],
                    ),
                )
            )

    for report in _readable_reports():
        score = _match_score(text, report["label"], report["aliases"])
        if score:
            routes.append(
                (
                    score,
                    DiscoveredRoute(
                        name=f"report:{report['name']}",
                        label=f"{report['label']} Report",
                        route=("query-report", report["name"]),
                        category="report",
                        required_doctype=report.get("ref_doctype"),
                    ),
                )
            )

    for workspace in _workspaces():
        score = _match_score(text, workspace["label"], workspace["aliases"])
        if score:
            routes.append(
                (
                    score,
                    DiscoveredRoute(
                        name=f"workspace:{workspace['name']}",
                        label=f"{workspace['label']} Workspace",
                        route=(_slug(workspace["name"]),),
                        category="workspace",
                    ),
                )
            )

    for page in _pages():
        score = _match_score(text, page["label"], page["aliases"])
        if score:
            routes.append(
                (
                    score,
                    DiscoveredRoute(
                        name=f"page:{page['name']}",
                        label=f"{page['label']} Page",
                        route=(page["name"],),
                        category="page",
                    ),
                )
            )

    for module in _modules():
        score = _match_score(text, module["label"], module["aliases"])
        if score:
            routes.append(
                (
                    score,
                    DiscoveredRoute(
                        name=f"module:{module['name']}",
                        label=f"{module['label']} Module",
                        route=(_slug(module["name"]),),
                        category="module",
                    ),
                )
            )

    for dashboard in _dashboards():
        score = _match_score(text, dashboard["label"], dashboard["aliases"])
        if score:
            routes.append(
                (
                    score,
                    DiscoveredRoute(
                        name=f"dashboard:{dashboard['name']}",
                        label=f"{dashboard['label']} Dashboard",
                        route=("dashboard-view", dashboard["name"]),
                        category="dashboard",
                    ),
                )
            )

    ranked = sorted(routes, key=lambda item: item[0], reverse=True)
    return [route for _, route in ranked[:limit]]


def find_specific_document(question: str) -> DiscoveredRoute | None:
    text = canonical_text(question)
    doctype = find_readable_doctype(question)
    if not doctype:
        return None

    document_name = _extract_document_name(text)
    filters: dict[str, Any] = {}
    order_by = "modified desc"

    if document_name:
        filters["name"] = ["like", f"%{document_name}%"]
    elif any(term in text for term in ("last", "latest", "recent", "akhri", "pichla", "\u0622\u062e\u0631\u06cc")):
        order_by = "creation desc"
    else:
        return None

    rows = frappe.get_list(
        doctype["name"],
        filters=filters,
        fields=["name"],
        order_by=order_by,
        limit_page_length=2,
    )

    if not rows:
        return None

    if len(rows) > 1 and document_name:
        return DiscoveredRoute(
            name=f"ambiguous:{doctype['name']}",
            label=f"Multiple {doctype['label']} records",
            route=("List", doctype["name"]),
            category="ambiguous",
            required_doctype=doctype["name"],
        )

    name = rows[0]["name"]
    return DiscoveredRoute(
        name=f"document:{doctype['name']}:{name}",
        label=f"{doctype['label']} {name}",
        route=("Form", doctype["name"], name),
        category="document",
        required_doctype=doctype["name"],
    )


def find_readable_doctype(question: str) -> dict[str, Any] | None:
    text = canonical_text(question)
    matches = []

    for doctype in _readable_doctypes():
        score = _match_score(text, doctype["label"], doctype["aliases"])
        if score:
            matches.append((score, doctype))

    if not matches:
        return None

    return sorted(matches, key=lambda item: item[0], reverse=True)[0][1]


def safe_list_fields(doctype: str) -> list[str]:
    meta = frappe.get_meta(doctype)
    fields = ["name"]

    for candidate in (meta.title_field, "status", "customer_name", "supplier_name", "item_name"):
        if candidate and candidate not in fields and meta.has_field(candidate):
            fields.append(candidate)

    if meta.has_field("modified"):
        fields.append("modified")

    return fields[:5]


def _readable_doctypes() -> list[dict[str, Any]]:
    doctypes = frappe.get_all(
        "DocType",
        filters={"istable": 0},
        fields=["name", "module", "custom"],
        order_by="name asc",
        limit_page_length=1000,
    )
    readable = []

    for doctype in doctypes:
        name = doctype["name"]
        if not can_read_doctype(name):
            continue

        label = name.replace("_", " ")
        readable.append(
            {
                "name": name,
                "label": label,
                "module": doctype.get("module"),
                "custom": doctype.get("custom"),
                "aliases": _aliases_for_label(label),
            }
        )

    return readable


def _readable_reports() -> list[dict[str, Any]]:
    reports = frappe.get_all(
        "Report",
        filters={"disabled": 0},
        fields=["name", "report_name", "ref_doctype"],
        order_by="name asc",
        limit_page_length=1000,
    )
    readable = []

    for report in reports:
        ref_doctype = report.get("ref_doctype")
        if ref_doctype and not can_read_doctype(ref_doctype):
            continue

        label = report.get("report_name") or report["name"]
        readable.append(
            {
                "name": report["name"],
                "label": label,
                "ref_doctype": ref_doctype,
                "aliases": _aliases_for_label(label),
            }
        )

    return readable


def _workspaces() -> list[dict[str, Any]]:
    workspaces = frappe.get_all(
        "Workspace",
        filters={"is_hidden": 0},
        fields=["name", "label", "module"],
        order_by="sequence_id asc, name asc",
        limit_page_length=500,
    )

    return [
        {
            "name": workspace["name"],
            "label": workspace.get("label") or workspace["name"],
            "module": workspace.get("module"),
            "aliases": _aliases_for_label(workspace.get("label") or workspace["name"]),
        }
        for workspace in workspaces
    ]


def _dashboards() -> list[dict[str, Any]]:
    if not frappe.db.exists("DocType", "Dashboard"):
        return []

    dashboards = frappe.get_all(
        "Dashboard",
        fields=["name", "dashboard_name", "module"],
        order_by="name asc",
        limit_page_length=500,
    )
    return [
        {
            "name": dashboard["name"],
            "label": dashboard.get("dashboard_name") or dashboard["name"],
            "module": dashboard.get("module"),
            "aliases": _aliases_for_label(dashboard.get("dashboard_name") or dashboard["name"]),
        }
        for dashboard in dashboards
    ]


def _pages() -> list[dict[str, Any]]:
    pages = frappe.get_all(
        "Page",
        fields=["name", "title", "module"],
        order_by="title asc, name asc",
        limit_page_length=500,
    )
    return [
        {
            "name": page["name"],
            "label": page.get("title") or page["name"],
            "module": page.get("module"),
            "aliases": _aliases_for_label(page.get("title") or page["name"]),
        }
        for page in pages
    ]


def _modules() -> list[dict[str, Any]]:
    modules = frappe.get_all(
        "Module Def",
        fields=["name", "module_name"],
        order_by="module_name asc, name asc",
        limit_page_length=500,
    )
    return [
        {
            "name": module["name"],
            "label": module.get("module_name") or module["name"],
            "aliases": _aliases_for_label(module.get("module_name") or module["name"]),
        }
        for module in modules
    ]


def _aliases_for_label(label: str) -> tuple[str, ...]:
    return business_aliases_for_label(label)


def _match_score(text: str, label: str, aliases: tuple[str, ...]) -> int:
    score = fuzzy_match_score(text, label, aliases)
    return score if score >= 45 else 0


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _extract_document_name(text: str) -> str | None:
    markers = (" named ", " name ", " number ", " no ", " id ", " code ")
    for marker in markers:
        if marker in text:
            value = text[text.rfind(marker) + len(marker) :].strip()
            return value[:120] or None

    tokens = text.split()
    candidates = [token for token in tokens if any(char.isdigit() for char in token) or "-" in token or "/" in token]
    return candidates[-1] if candidates else None

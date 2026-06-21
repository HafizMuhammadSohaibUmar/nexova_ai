from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import frappe

from nexova_ai.assistant.permissions import can_read_doctype
from nexova_ai.assistant.vocabulary import business_aliases_for_label, canonical_text, fuzzy_match_score


METADATA_CACHE_KEY = "nexova_ai:metadata:v1"
SAFE_FIELD_TYPES = {
    "Data",
    "Link",
    "Dynamic Link",
    "Select",
    "Int",
    "Float",
    "Currency",
    "Percent",
    "Date",
    "Datetime",
    "Check",
    "Small Text",
    "Text",
    "Long Text",
    "Read Only",
}


@dataclass(frozen=True)
class FieldSummary:
    fieldname: str
    label: str
    fieldtype: str
    required: bool = False
    options: str | None = None
    hidden: bool = False
    read_only: bool = False
    in_list_view: bool = False


@dataclass(frozen=True)
class DocTypeSummary:
    name: str
    label: str
    module: str | None = None
    title_field: str | None = None
    is_submittable: bool = False
    can_read: bool = False
    can_create: bool = False
    can_write: bool = False
    can_delete: bool = False
    can_submit: bool = False
    fields: tuple[FieldSummary, ...] = field(default_factory=tuple)
    required_fields: tuple[str, ...] = field(default_factory=tuple)
    link_fields: tuple[FieldSummary, ...] = field(default_factory=tuple)
    table_fields: tuple[FieldSummary, ...] = field(default_factory=tuple)
    safe_list_fields: tuple[str, ...] = field(default_factory=tuple)
    safe_filter_fields: tuple[str, ...] = field(default_factory=tuple)
    safe_numeric_fields: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "module": self.module,
            "title_field": self.title_field,
            "is_submittable": self.is_submittable,
            "permissions": {
                "read": self.can_read,
                "create": self.can_create,
                "write": self.can_write,
                "delete": self.can_delete,
                "submit": self.can_submit,
            },
            "required_fields": list(self.required_fields),
            "link_fields": [field.fieldname for field in self.link_fields],
            "table_fields": [field.fieldname for field in self.table_fields],
            "safe_list_fields": list(self.safe_list_fields),
            "safe_filter_fields": list(self.safe_filter_fields),
            "safe_numeric_fields": list(self.safe_numeric_fields),
        }


def get_doctype_summary(doctype: str) -> DocTypeSummary:
    meta = frappe.get_meta(doctype)
    fields = tuple(_field_summary(field) for field in meta.fields)
    required_fields = tuple(field.fieldname for field in fields if field.required and not field.hidden)
    link_fields = tuple(field for field in fields if field.fieldtype in {"Link", "Dynamic Link"})
    table_fields = tuple(field for field in fields if field.fieldtype in {"Table", "Table MultiSelect"})
    safe_list_fields = _safe_list_fields(meta, fields)
    safe_filter_fields = tuple(
        field.fieldname
        for field in fields
        if field.fieldtype in SAFE_FIELD_TYPES and not field.hidden
    )
    safe_numeric_fields = tuple(
        field.fieldname
        for field in fields
        if field.fieldtype in {"Int", "Float", "Currency", "Percent"} and not field.hidden
    )

    return DocTypeSummary(
        name=doctype,
        label=getattr(meta, "name", doctype).replace("_", " "),
        module=getattr(meta, "module", None),
        title_field=getattr(meta, "title_field", None),
        is_submittable=bool(getattr(meta, "is_submittable", False)),
        can_read=can_read_doctype(doctype),
        can_create=_has_permission(doctype, "create"),
        can_write=_has_permission(doctype, "write"),
        can_delete=_has_permission(doctype, "delete"),
        can_submit=_has_permission(doctype, "submit"),
        fields=fields,
        required_fields=required_fields,
        link_fields=link_fields,
        table_fields=table_fields,
        safe_list_fields=safe_list_fields,
        safe_filter_fields=safe_filter_fields,
        safe_numeric_fields=safe_numeric_fields,
    )


def find_doctype_matches(question: str, limit: int = 5) -> list[tuple[int, DocTypeSummary]]:
    text = canonical_text(question)
    matches: list[tuple[int, str]] = []

    for row in frappe.get_all(
        "DocType",
        filters={"istable": 0},
        fields=["name"],
        order_by="name asc",
        limit_page_length=1000,
    ):
        doctype = row["name"]
        if not can_read_doctype(doctype):
            continue

        aliases = business_aliases_for_label(doctype)
        score = fuzzy_match_score(text, doctype, aliases)
        if score >= 45:
            matches.append((score, doctype))

    return [
        (score, get_doctype_summary(doctype))
        for score, doctype in sorted(matches, key=lambda item: item[0], reverse=True)[:limit]
    ]


def find_doctype_by_phrase(question: str, limit: int = 5) -> list[DocTypeSummary]:
    return [summary for _, summary in find_doctype_matches(question, limit=limit)]


def describe_allowed_actions(doctype: str) -> dict[str, bool]:
    summary = get_doctype_summary(doctype)
    return {
        "read": summary.can_read,
        "create": summary.can_create,
        "write": summary.can_write,
        "delete": summary.can_delete,
        "submit": summary.can_submit,
    }


def _field_summary(field: Any) -> FieldSummary:
    return FieldSummary(
        fieldname=field.fieldname,
        label=field.label or field.fieldname.replace("_", " ").title(),
        fieldtype=field.fieldtype,
        required=bool(getattr(field, "reqd", 0)),
        options=getattr(field, "options", None),
        hidden=bool(getattr(field, "hidden", 0)),
        read_only=bool(getattr(field, "read_only", 0)),
        in_list_view=bool(getattr(field, "in_list_view", 0)),
    )


def _safe_list_fields(meta: Any, fields: tuple[FieldSummary, ...]) -> tuple[str, ...]:
    selected = ["name"]

    for candidate in (
        getattr(meta, "title_field", None),
        "status",
        "customer_name",
        "supplier_name",
        "item_name",
        "posting_date",
        "transaction_date",
        "modified",
    ):
        if candidate and candidate not in selected and meta.has_field(candidate):
            selected.append(candidate)

    for field in fields:
        if len(selected) >= 6:
            break
        if field.in_list_view and field.fieldname not in selected and not field.hidden:
            selected.append(field.fieldname)

    return tuple(selected[:6])


def _has_permission(doctype: str, ptype: str) -> bool:
    try:
        return bool(frappe.has_permission(doctype=doctype, ptype=ptype))
    except Exception:
        return False

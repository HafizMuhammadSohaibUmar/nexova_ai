from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import frappe

from nexova_ai.assistant.contracts import response
from nexova_ai.assistant.metadata import get_doctype_summary


@dataclass(frozen=True)
class ActionDraft:
    action: str
    doctype: str
    fields: dict[str, Any]
    child_tables: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    missing_required_fields: tuple[str, ...] = field(default_factory=tuple)
    requires_confirmation: bool = True
    execution_enabled: bool = False
    risk_level: str = "medium"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_create_draft(
    doctype: str,
    fields: dict[str, Any],
    child_tables: dict[str, list[dict[str, Any]]] | None = None,
) -> ActionDraft:
    summary = get_doctype_summary(doctype)
    if not summary.can_create:
        raise frappe.PermissionError(f"No create permission for {doctype}")

    allowed_fields = {
        field.fieldname
        for field in summary.fields
        if not field.hidden and not field.read_only and field.fieldtype not in {"Section Break", "Column Break", "Tab Break"}
    }
    clean_fields = {key: value for key, value in fields.items() if key in allowed_fields}
    missing = tuple(field for field in summary.required_fields if field not in clean_fields)

    return ActionDraft(
        action="create",
        doctype=doctype,
        fields=clean_fields,
        child_tables=child_tables or {},
        missing_required_fields=missing,
        risk_level="high" if summary.is_submittable else "medium",
    )


def preview_create_action(
    doctype: str,
    fields: dict[str, Any],
    child_tables: dict[str, list[dict[str, Any]]] | None = None,
):
    draft = build_create_draft(doctype, fields, child_tables)
    message = f"I prepared a draft {doctype}. Review and confirm before anything is saved."
    if draft.missing_required_fields:
        message = (
            f"I can prepare a draft {doctype}, but required field(s) are missing: "
            + ", ".join(draft.missing_required_fields)
            + "."
        )

    return response(
        message,
        status="Draft",
        intent="action_preview",
        tool_name="safe_crud_draft",
        data={
            "type": "action_preview",
            "draft": draft.as_dict(),
            "confirmation_required": True,
            "execution_note": "Writes are intentionally disabled until a separate confirmation flow is implemented.",
        },
    )


def execute_confirmed_action(action_id: str | None = None):
    return response(
        "Confirmed write execution is not enabled yet. The assistant can only prepare safe previews at this stage.",
        status="Blocked",
        intent="action_execution_disabled",
        tool_name="safe_crud_draft",
        data={"action_id": action_id, "writes_enabled": False},
    )

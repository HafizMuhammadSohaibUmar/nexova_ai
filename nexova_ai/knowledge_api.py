from __future__ import annotations

import frappe

from nexova_ai.assistant.knowledge import rebuild_document_chunks


@frappe.whitelist()
def rebuild_knowledge_document(document_name: str) -> dict[str, int]:
    if "System Manager" not in set(frappe.get_roles()):
        raise frappe.PermissionError

    return {"chunk_count": rebuild_document_chunks(document_name)}

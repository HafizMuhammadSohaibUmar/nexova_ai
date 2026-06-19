from __future__ import annotations

import hashlib

import frappe

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150


def chunk_text(text: str, *, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    clean = " ".join((text or "").split())
    if not clean:
        return []

    chunks: list[str] = []
    start = 0

    while start < len(clean):
        end = min(start + chunk_size, len(clean))
        chunks.append(clean[start:end])
        if end == len(clean):
            break
        start = max(end - overlap, start + 1)

    return chunks


def rebuild_document_chunks(document_name: str) -> int:
    document = frappe.get_doc("Nexova AI Knowledge Document", document_name)

    if document.status != "Approved":
        frappe.throw("Only approved knowledge documents can be indexed.")

    existing = frappe.get_all(
        "Nexova AI Knowledge Chunk",
        filters={"knowledge_document": document.name},
        pluck="name",
    )

    for chunk_name in existing:
        frappe.delete_doc("Nexova AI Knowledge Chunk", chunk_name, ignore_permissions=True)

    chunks = chunk_text(document.content or "")

    for index, chunk in enumerate(chunks, start=1):
        frappe.get_doc(
            {
                "doctype": "Nexova AI Knowledge Chunk",
                "knowledge_source": document.knowledge_source,
                "knowledge_document": document.name,
                "chunk_index": index,
                "content": chunk,
                "content_hash": hashlib.sha256(chunk.encode("utf-8")).hexdigest(),
                "enabled": 1,
            }
        ).insert(ignore_permissions=True)

    document.chunk_count = len(chunks)
    document.index_status = "Indexed" if chunks else "No Content"
    document.save(ignore_permissions=True)

    return len(chunks)

import frappe
from frappe.model.document import Document


class NexovaAIKnowledgeChunk(Document):
    def autoname(self):
        self.name = f"NAI-CHUNK-{frappe.generate_hash(length=10)}"

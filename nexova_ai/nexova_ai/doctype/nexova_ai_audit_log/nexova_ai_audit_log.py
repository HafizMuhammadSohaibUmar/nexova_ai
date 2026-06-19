import frappe
from frappe.model.document import Document


class NexovaAIAuditLog(Document):
    def autoname(self):
        self.name = f"NAI-AUDIT-{frappe.generate_hash(length=10)}"

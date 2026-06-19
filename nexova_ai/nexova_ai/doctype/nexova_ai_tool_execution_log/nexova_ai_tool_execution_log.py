import frappe
from frappe.model.document import Document


class NexovaAIToolExecutionLog(Document):
    def autoname(self):
        self.name = f"NAI-TOOL-{frappe.generate_hash(length=10)}"

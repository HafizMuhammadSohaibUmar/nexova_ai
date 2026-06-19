from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "nexova_ai"
PACKAGE = APP / "nexova_ai"
PAGE = PACKAGE / "page" / "nexova_ai_assistant"
DOCTYPE = PACKAGE / "doctype"
WORKSPACE = PACKAGE / "workspace" / "nexova_ai" / "nexova_ai.json"
HOOKS = APP / "hooks.py"
PATCHES = APP / "patches.txt"
ASSISTANT = APP / "assistant"


def _load_hooks() -> dict[str, object]:
    module = ast.parse(HOOKS.read_text(encoding="utf-8"))
    values: dict[str, object] = {}

    for node in module.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                try:
                    values[target.id] = ast.literal_eval(node.value)
                except ValueError:
                    continue

    return values


class AppStructureTest(unittest.TestCase):
    def test_standard_page_export_structure(self) -> None:
        self.assertTrue((PAGE / "__init__.py").exists())
        self.assertTrue((PAGE / "nexova_ai_assistant.py").exists())
        self.assertTrue((PAGE / "nexova_ai_assistant.js").exists())
        self.assertTrue((PAGE / "nexova_ai_assistant.json").exists())

    def test_page_json_uses_unique_assistant_route(self) -> None:
        page = json.loads((PAGE / "nexova_ai_assistant.json").read_text(encoding="utf-8"))

        self.assertEqual(page["doctype"], "Page")
        self.assertEqual(page["module"], "Nexova AI")
        self.assertEqual(page["name"], "nexova-ai-assistant")
        self.assertEqual(page["page_name"], "nexova-ai-assistant")
        self.assertEqual(page["standard"], "Yes")

    def test_workspace_links_to_assistant_page_without_route_conflict(self) -> None:
        workspace = json.loads(WORKSPACE.read_text(encoding="utf-8"))
        content = json.loads(workspace["content"])

        shortcuts = {block["data"]["shortcut_name"]: block for block in content if block["type"] == "shortcut"}
        self.assertEqual(workspace["name"], "Nexova AI")
        self.assertEqual(workspace["module"], "Nexova AI")
        self.assertEqual(shortcuts["Open Nexova AI"]["data"]["link_to"], "nexova-ai-assistant")
        self.assertEqual(shortcuts["Open Nexova AI"]["data"]["route"], "/app/nexova-ai-assistant")
        self.assertEqual(shortcuts["Nexova AI Settings"]["data"]["link_to"], "Nexova AI Settings")
        self.assertEqual(shortcuts["Nexova AI Audit Log"]["data"]["link_to"], "Nexova AI Audit Log")
        self.assertEqual(workspace["shortcuts"][0]["link_to"], "nexova-ai-assistant")

    def test_hooks_do_not_preload_page_controller(self) -> None:
        hooks = _load_hooks()

        self.assertEqual(hooks["app_name"], "nexova_ai")
        self.assertEqual(hooks["required_apps"], ["erpnext"])
        self.assertEqual(hooks["app_include_css"], "/assets/nexova_ai/css/nexova_ai.css")
        self.assertNotIn("app_include_js", hooks)
        self.assertNotIn("page_js", hooks)

    def test_page_controller_registers_only_assistant_route(self) -> None:
        script = (PAGE / "nexova_ai_assistant.js").read_text(encoding="utf-8")

        self.assertIn('frappe.pages["nexova-ai-assistant"]', script)
        self.assertNotIn('frappe.pages["nexova-ai"]', script)
        self.assertIn("frappe.ui.make_app_page", script)

    def test_workspace_route_patch_is_registered(self) -> None:
        patches = PATCHES.read_text(encoding="utf-8").splitlines()

        self.assertIn(
            "nexova_ai.patches.v0_0.update_workspace_shortcut_route",
            patches,
        )

    def test_api_uses_supported_role_check(self) -> None:
        source = (ASSISTANT / "permissions.py").read_text(encoding="utf-8")

        self.assertNotIn("frappe.has_role", source)
        self.assertIn("frappe.get_roles()", source)

    def test_api_accepts_common_receivables_voice_variants(self) -> None:
        source = (ASSISTANT / "intent.py").read_text(encoding="utf-8")

        self.assertIn('"receiveables"', source)
        self.assertIn('"recievables"', source)
        self.assertIn('"recievable"', source)
        self.assertIn('"unpaid"', source)

    def test_production_foundation_doctypes_exist(self) -> None:
        settings = DOCTYPE / "nexova_ai_settings" / "nexova_ai_settings.json"
        audit_log = DOCTYPE / "nexova_ai_audit_log" / "nexova_ai_audit_log.json"
        tool_log = DOCTYPE / "nexova_ai_tool_execution_log" / "nexova_ai_tool_execution_log.json"

        self.assertTrue(settings.exists())
        self.assertTrue(audit_log.exists())
        self.assertTrue(tool_log.exists())

        settings_doc = json.loads(settings.read_text(encoding="utf-8"))
        audit_log_doc = json.loads(audit_log.read_text(encoding="utf-8"))
        tool_log_doc = json.loads(tool_log.read_text(encoding="utf-8"))

        self.assertEqual(settings_doc["name"], "Nexova AI Settings")
        self.assertEqual(settings_doc["issingle"], 1)
        self.assertEqual(audit_log_doc["name"], "Nexova AI Audit Log")
        self.assertIn("question", audit_log_doc["field_order"])
        self.assertEqual(tool_log_doc["name"], "Nexova AI Tool Execution Log")

    def test_api_uses_settings_and_audit_log(self) -> None:
        settings_source = (ASSISTANT / "settings.py").read_text(encoding="utf-8")
        audit_source = (ASSISTANT / "audit.py").read_text(encoding="utf-8")
        orchestrator_source = (ASSISTANT / "orchestrator.py").read_text(encoding="utf-8")

        self.assertIn('"Nexova AI Settings"', settings_source)
        self.assertIn('"Nexova AI Audit Log"', audit_source)
        self.assertIn("log_request", orchestrator_source)

    def test_assistant_architecture_modules_exist(self) -> None:
        for module in (
            "contracts.py",
            "settings.py",
            "permissions.py",
            "safety.py",
            "rate_limit.py",
            "intent.py",
            "registry.py",
            "tools.py",
            "navigation.py",
            "rag.py",
            "knowledge.py",
            "voice.py",
            "orchestrator.py",
        ):
            self.assertTrue((ASSISTANT / module).exists(), module)

    def test_tool_registry_contains_production_v1_tools(self) -> None:
        source = (ASSISTANT / "registry.py").read_text(encoding="utf-8")

        for tool_name in (
            "sales_summary",
            "purchase_summary",
            "stock_balance",
            "receivables_summary",
            "payables_summary",
            "customer_summary",
            "supplier_summary",
            "item_lookup",
            "quotation_summary",
            "sales_order_summary",
            "purchase_order_summary",
            "invoice_summary",
        ):
            self.assertIn(tool_name, source)

    def test_rag_doctypes_exist(self) -> None:
        for doctype in (
            "nexova_ai_knowledge_source",
            "nexova_ai_knowledge_document",
            "nexova_ai_knowledge_chunk",
        ):
            self.assertTrue((DOCTYPE / doctype / f"{doctype}.json").exists(), doctype)

    def test_frontend_handles_backend_navigation(self) -> None:
        script = (PAGE / "nexova_ai_assistant.js").read_text(encoding="utf-8")

        self.assertIn("handleAction(data)", script)
        self.assertIn("frappe.set_route.apply", script)
        self.assertIn("renderStructuredData(data", script)

    def test_frontend_requires_voice_transcript_confirmation(self) -> None:
        script = (PAGE / "nexova_ai_assistant.js").read_text(encoding="utf-8")

        self.assertIn("Transcript ready. Review it, then tap Ask.", script)
        self.assertNotIn("askQuestion(transcript);", script)

    def test_live_tools_include_date_and_entity_filters(self) -> None:
        source = (ASSISTANT / "tools.py").read_text(encoding="utf-8")

        self.assertIn("_date_range_from_question", source)
        self.assertIn("_invoice_context", source)
        self.assertIn("filters_applied", source)
        self.assertIn('"customer"', source)
        self.assertIn('"supplier"', source)
        self.assertIn('"warehouse"', source)

    def test_live_tools_return_structured_cards_and_tables(self) -> None:
        source = (ASSISTANT / "tools.py").read_text(encoding="utf-8")
        css = (APP / "public" / "css" / "nexova_ai.css").read_text(encoding="utf-8")
        script = (PAGE / "nexova_ai_assistant.js").read_text(encoding="utf-8")

        self.assertIn('"summary_cards"', source)
        self.assertIn('"table"', source)
        self.assertIn("_party_table", source)
        self.assertIn("nexova-ai-result-card", css)
        self.assertIn("nexova-ai-result-table", css)
        self.assertIn("data.table.rows.slice(0, 10)", script)


if __name__ == "__main__":
    unittest.main()

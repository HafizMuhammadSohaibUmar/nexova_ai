from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "nexova_ai"
PACKAGE = APP / "nexova_ai"
PAGE = PACKAGE / "page" / "nexova_ai_assistant"
WORKSPACE = PACKAGE / "workspace" / "nexova_ai" / "nexova_ai.json"
HOOKS = APP / "hooks.py"
PATCHES = APP / "patches.txt"


def _load_hooks() -> dict[str, object]:
    module = ast.parse(HOOKS.read_text())
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
        page = json.loads((PAGE / "nexova_ai_assistant.json").read_text())

        self.assertEqual(page["doctype"], "Page")
        self.assertEqual(page["module"], "Nexova AI")
        self.assertEqual(page["name"], "nexova-ai-assistant")
        self.assertEqual(page["page_name"], "nexova-ai-assistant")
        self.assertEqual(page["standard"], "Yes")

    def test_workspace_links_to_assistant_page_without_route_conflict(self) -> None:
        workspace = json.loads(WORKSPACE.read_text())
        content = json.loads(workspace["content"])

        shortcut = next(block for block in content if block["type"] == "shortcut")
        self.assertEqual(workspace["name"], "Nexova AI")
        self.assertEqual(workspace["module"], "Nexova AI")
        self.assertEqual(shortcut["data"]["link_to"], "nexova-ai-assistant")
        self.assertEqual(shortcut["data"]["route"], "/app/nexova-ai-assistant")
        self.assertEqual(workspace["shortcuts"][0]["link_to"], "nexova-ai-assistant")

    def test_hooks_do_not_preload_page_controller(self) -> None:
        hooks = _load_hooks()

        self.assertEqual(hooks["app_name"], "nexova_ai")
        self.assertEqual(hooks["required_apps"], ["erpnext"])
        self.assertEqual(hooks["app_include_css"], "/assets/nexova_ai/css/nexova_ai.css")
        self.assertNotIn("app_include_js", hooks)
        self.assertNotIn("page_js", hooks)

    def test_page_controller_registers_only_assistant_route(self) -> None:
        script = (PAGE / "nexova_ai_assistant.js").read_text()

        self.assertIn('frappe.pages["nexova-ai-assistant"]', script)
        self.assertNotIn('frappe.pages["nexova-ai"]', script)
        self.assertIn("frappe.ui.make_app_page", script)

    def test_workspace_route_patch_is_registered(self) -> None:
        patches = PATCHES.read_text().splitlines()

        self.assertIn(
            "nexova_ai.patches.v0_0.update_workspace_shortcut_route",
            patches,
        )

    def test_api_uses_supported_role_check(self) -> None:
        source = (APP / "api.py").read_text()

        self.assertNotIn("frappe.has_role", source)
        self.assertIn("frappe.get_roles()", source)

    def test_api_accepts_common_receivables_voice_variants(self) -> None:
        source = (APP / "api.py").read_text()

        self.assertIn('"receiveables"', source)
        self.assertIn('"recievables"', source)
        self.assertIn('"recievable"', source)
        self.assertIn('"unpaid"', source)


if __name__ == "__main__":
    unittest.main()

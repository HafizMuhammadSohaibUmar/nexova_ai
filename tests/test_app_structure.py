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
DEPLOY_AI = ROOT / "deploy" / "ai"


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
        self.assertEqual(workspace["label"], "Invoxia AI")
        self.assertEqual(workspace["title"], "Invoxia AI")
        self.assertEqual(shortcuts["Open Invoxia AI"]["data"]["link_to"], "nexova-ai-assistant")
        self.assertEqual(shortcuts["Open Invoxia AI"]["data"]["route"], "/app/nexova-ai-assistant")
        self.assertEqual(shortcuts["Invoxia AI Settings"]["data"]["link_to"], "Nexova AI Settings")
        self.assertEqual(shortcuts["Invoxia AI Audit Log"]["data"]["link_to"], "Nexova AI Audit Log")
        self.assertEqual(workspace["shortcuts"][0]["link_to"], "nexova-ai-assistant")

    def test_hooks_do_not_preload_page_controller(self) -> None:
        hooks = _load_hooks()

        self.assertEqual(hooks["app_name"], "nexova_ai")
        self.assertEqual(hooks["required_apps"], ["erpnext"])
        self.assertEqual(hooks["app_include_css"], "/assets/nexova_ai/css/nexova_ai.css")
        self.assertNotIn("app_include_js", hooks)
        self.assertNotIn("page_js", hooks)
        self.assertIn(
            "nexova_ai.assistant.retention.cleanup_audit_logs",
            hooks["scheduler_events"]["daily"],
        )
        self.assertEqual(
            hooks["doc_events"]["*"]["before_save"],
            "nexova_ai.assistant.read_only.enforce_write_allowed",
        )
        self.assertEqual(
            hooks["doc_events"]["*"]["before_submit"],
            "nexova_ai.assistant.read_only.enforce_write_allowed",
        )

    def test_page_controller_registers_only_assistant_route(self) -> None:
        script = (PAGE / "nexova_ai_assistant.js").read_text(encoding="utf-8")

        self.assertIn('frappe.pages["nexova-ai-assistant"]', script)
        self.assertNotIn('frappe.pages["nexova-ai"]', script)
        self.assertIn("frappe.ui.make_app_page", script)
        self.assertIn('title: __("Invoxia AI")', script)
        self.assertIn("invoxia-mark.svg", script)

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
        source = (ASSISTANT / "vocabulary.py").read_text(encoding="utf-8")

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

    def test_settings_contains_production_control_fields(self) -> None:
        settings = DOCTYPE / "nexova_ai_settings" / "nexova_ai_settings.json"
        settings_doc = json.loads(settings.read_text(encoding="utf-8"))
        fieldnames = {field["fieldname"] for field in settings_doc["fields"]}

        for fieldname in (
            "audit_log_retention_days",
            "tool_log_retention_days",
            "max_tool_rows",
            "max_dynamic_rows",
            "max_response_characters",
            "subscription_grace_period_days",
        ):
            self.assertIn(fieldname, fieldnames)

    def test_settings_contains_cloud_and_local_provider_fields(self) -> None:
        settings = DOCTYPE / "nexova_ai_settings" / "nexova_ai_settings.json"
        settings_doc = json.loads(settings.read_text(encoding="utf-8"))
        fields = {field["fieldname"]: field for field in settings_doc["fields"]}

        for fieldname in (
            "deployment_mode",
            "license_mode",
            "stt_provider",
            "llm_provider",
            "rag_provider",
            "local_stt_endpoint",
            "local_llm_endpoint",
            "local_llm_model",
            "cloud_stt_provider",
            "cloud_llm_provider",
        ):
            self.assertIn(fieldname, fields)

        self.assertIn("Local Offline", fields["deployment_mode"]["options"])
        self.assertIn("Signed Offline License", fields["license_mode"]["options"])
        self.assertIn("Local Whisper", fields["stt_provider"]["options"])
        self.assertIn("Cloud Deepgram", fields["stt_provider"]["options"])
        self.assertIn("Local Ollama", fields["llm_provider"]["options"])
        self.assertEqual(fields["local_llm_model"]["default"], "qwen3:8b")
        self.assertIn("Local", fields["rag_provider"]["options"])

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
            "subscription.py",
            "intent.py",
            "vocabulary.py",
            "registry.py",
            "discovery.py",
            "dynamic_tools.py",
            "metadata.py",
            "query_engine.py",
            "actions.py",
            "license.py",
            "read_only.py",
            "providers.py",
            "tools.py",
            "navigation.py",
            "rag.py",
            "knowledge.py",
            "voice.py",
            "stt.py",
            "llm.py",
            "retention.py",
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
            "profit_and_loss",
            "cash_bank_balance",
            "account_balance",
            "party_ledger",
            "item_wise_sales",
            "customer_wise_sales",
            "low_stock",
            "slow_moving_items",
            "gross_profit",
            "expenses_summary",
            "payroll_summary",
            "attendance_summary",
            "manufacturing_summary",
            "crm_summary",
            "project_summary",
            "asset_summary",
            "tax_summary",
            "trend_analysis",
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

    def test_dynamic_discovery_foundation_exists(self) -> None:
        discovery = (ASSISTANT / "discovery.py").read_text(encoding="utf-8")
        dynamic_tools = (ASSISTANT / "dynamic_tools.py").read_text(encoding="utf-8")
        navigation = (ASSISTANT / "navigation.py").read_text(encoding="utf-8")
        orchestrator = (ASSISTANT / "orchestrator.py").read_text(encoding="utf-8")

        self.assertIn("find_navigation_routes", discovery)
        self.assertIn("find_specific_document", discovery)
        self.assertIn("_dashboards", discovery)
        self.assertIn("_pages", discovery)
        self.assertIn("_modules", discovery)
        self.assertIn("find_readable_doctype", discovery)
        self.assertIn("safe_list_fields", discovery)
        self.assertIn("fuzzy_match_score", discovery)
        self.assertIn("answer_dynamic_query", dynamic_tools)
        self.assertIn("plan_dynamic_query", dynamic_tools)
        self.assertIn("execute_query_plan", dynamic_tools)
        self.assertIn("dynamic_doctype_list", dynamic_tools)
        self.assertIn("dynamic_doctype_count", dynamic_tools)
        self.assertIn("find_navigation_routes", navigation)
        self.assertIn("route_options", navigation)
        self.assertIn("answer_dynamic_query", orchestrator)

    def test_navigation_frontend_applies_route_options(self) -> None:
        script = (PAGE / "nexova_ai_assistant.js").read_text(encoding="utf-8")

        self.assertIn("frappe.route_options", script)

    def test_llm_fallback_is_behind_registry(self) -> None:
        llm = (ASSISTANT / "llm.py").read_text(encoding="utf-8")
        orchestrator = (ASSISTANT / "orchestrator.py").read_text(encoding="utf-8")

        self.assertIn("TOOL_REGISTRY", llm)
        self.assertIn("suggest_intent", orchestrator)
        self.assertIn("suggest_intent_with_llm", orchestrator)
        self.assertIn("parse_intent_response", llm)
        self.assertIn('provider != "Local Ollama"', llm)
        self.assertIn("BUILTIN_ROUTER_INTENTS", llm)
        self.assertIn("approved_intents = set(TOOL_REGISTRY) | BUILTIN_ROUTER_INTENTS", llm)
        self.assertIn('"dynamic_query"', llm)
        self.assertIn('"navigation"', llm)
        self.assertIn('"format": "json"', llm)
        self.assertIn('provider in {"Disabled", "Deterministic"}', llm)

    def test_urdu_and_roman_urdu_core_phrases_exist(self) -> None:
        vocabulary = (ASSISTANT / "vocabulary.py").read_text(encoding="utf-8")
        tools = (ASSISTANT / "tools.py").read_text(encoding="utf-8")

        for phrase in ("kholo", "dikhao", "wasooli", "kharcha", "tankhwa", "آج", "اس مہینے"):
            self.assertIn(phrase, vocabulary + tools)

    def test_live_tools_cover_requested_erp_modules(self) -> None:
        source = (ASSISTANT / "tools.py").read_text(encoding="utf-8")

        for function_name in (
            "profit_and_loss",
            "cash_bank_balance",
            "account_balance",
            "party_ledger",
            "item_wise_sales",
            "low_stock",
            "expenses_summary",
            "payroll_summary",
            "attendance_summary",
            "manufacturing_summary",
            "crm_summary",
            "project_summary",
            "asset_summary",
            "tax_summary",
            "trend_analysis",
        ):
            self.assertIn(f"def {function_name}", source)

    def test_voice_strategy_reaches_frontend(self) -> None:
        api = (APP / "api.py").read_text(encoding="utf-8")
        voice = (ASSISTANT / "voice.py").read_text(encoding="utf-8")
        script = (PAGE / "nexova_ai_assistant.js").read_text(encoding="utf-8")

        self.assertIn("recognition_language", api)
        self.assertIn("supports_server_stt", api)
        self.assertIn("transcribe_audio", api)
        self.assertIn("recognition_language", voice)
        self.assertIn("Local Whisper", voice)
        self.assertIn("Cloud Deepgram", voice)
        self.assertIn("AudioContext", script)
        self.assertIn("voice.wav", script)
        self.assertIn("audio/wav", script)
        self.assertIn("nexova_ai.api.transcribe_audio", script)
        self.assertIn("FormData", script)
        self.assertIn("maxAlternatives = 5", script)
        self.assertIn("state.recognitionLanguage", script)

    def test_server_stt_connector_uses_local_whisper_safely(self) -> None:
        stt = (ASSISTANT / "stt.py").read_text(encoding="utf-8")

        self.assertIn("transcribe_audio_bytes", stt)
        self.assertIn("MAX_AUDIO_BYTES", stt)
        self.assertIn('stt_provider != "Local Whisper"', stt)
        self.assertIn('endpoint.rstrip("/") + "/inference"', stt)
        self.assertIn("multipart/form-data", stt)
        self.assertIn("Do not store", (ASSISTANT / "voice.py").read_text(encoding="utf-8"))

    def test_cloud_and_local_deployment_modes_documented(self) -> None:
        guide = ROOT / "docs" / "CLOUD_AND_LOCAL_DEPLOYMENT_MODES.md"
        source = guide.read_text(encoding="utf-8")

        self.assertIn("Cloud Hosted", source)
        self.assertIn("Local Offline", source)
        self.assertIn("Local Whisper", source)
        self.assertIn("Local Ollama", source)
        self.assertIn("Signed Offline License", source)

    def test_metadata_engine_foundation_exists(self) -> None:
        source = (ASSISTANT / "metadata.py").read_text(encoding="utf-8")

        self.assertIn("class DocTypeSummary", source)
        self.assertIn("class FieldSummary", source)
        self.assertIn("get_doctype_summary", source)
        self.assertIn("find_doctype_by_phrase", source)
        self.assertIn("required_fields", source)
        self.assertIn("link_fields", source)
        self.assertIn("table_fields", source)
        self.assertIn("safe_filter_fields", source)
        self.assertIn("frappe.get_meta", source)
        self.assertIn("frappe.has_permission", source)

    def test_dynamic_query_engine_uses_metadata_and_safe_operations(self) -> None:
        source = (ASSISTANT / "query_engine.py").read_text(encoding="utf-8")

        self.assertIn("class QueryPlan", source)
        self.assertIn("plan_dynamic_query", source)
        self.assertIn("execute_query_plan", source)
        self.assertIn('operation="count"', source)
        self.assertIn('operation="sum"', source)
        self.assertIn('operation="list"', source)
        self.assertIn("safe_numeric_fields", source)
        self.assertIn("frappe.get_list", source)
        self.assertNotIn("frappe.db.sql", source)

    def test_safe_crud_draft_requires_confirmation_and_disables_execution(self) -> None:
        source = (ASSISTANT / "actions.py").read_text(encoding="utf-8")

        self.assertIn("class ActionDraft", source)
        self.assertIn("build_create_draft", source)
        self.assertIn("preview_create_action", source)
        self.assertIn("requires_confirmation: bool = True", source)
        self.assertIn("execution_enabled: bool = False", source)
        self.assertIn("Confirmed write execution is not enabled yet", source)
        self.assertNotIn(".insert(", source)
        self.assertNotIn(".save(", source)

    def test_license_and_read_only_foundation_exists(self) -> None:
        license_source = (ASSISTANT / "license.py").read_text(encoding="utf-8")
        read_only_source = (ASSISTANT / "read_only.py").read_text(encoding="utf-8")

        self.assertIn("class LicenseDecision", license_source)
        self.assertIn("evaluate_license", license_source)
        self.assertIn("Signed Offline License", license_source)
        self.assertIn("erp_read_only=True", license_source)
        self.assertIn("allow_backup_export=True", license_source)
        self.assertIn("is_write_allowed", read_only_source)
        self.assertIn("enforce_write_allowed", read_only_source)
        self.assertIn("WRITE_OPERATIONS", read_only_source)
        self.assertIn("Nexova AI Settings", read_only_source)

    def test_provider_contracts_cover_local_and_cloud_options(self) -> None:
        source = (ASSISTANT / "providers.py").read_text(encoding="utf-8")

        self.assertIn("class ProviderCapability", source)
        self.assertIn("Local Whisper", source)
        self.assertIn("Local Vosk", source)
        self.assertIn("Cloud Deepgram", source)
        self.assertIn("Local Ollama", source)
        self.assertIn("Cloud Mistral", source)
        self.assertIn("sends_client_data_to_cloud", source)

    def test_safe_actions_setting_is_present_but_disabled_by_default(self) -> None:
        settings = DOCTYPE / "nexova_ai_settings" / "nexova_ai_settings.json"
        settings_doc = json.loads(settings.read_text(encoding="utf-8"))
        fields = {field["fieldname"]: field for field in settings_doc["fields"]}

        self.assertIn("safe_actions_enabled", fields)
        self.assertEqual(fields["safe_actions_enabled"]["default"], "0")
        self.assertIn("safe_actions_enabled", (ASSISTANT / "settings.py").read_text(encoding="utf-8"))

    def test_subscription_grace_period_is_seven_days_by_default(self) -> None:
        settings = DOCTYPE / "nexova_ai_settings" / "nexova_ai_settings.json"
        settings_doc = json.loads(settings.read_text(encoding="utf-8"))
        fields = {field["fieldname"]: field for field in settings_doc["fields"]}

        self.assertIn("subscription_grace_period_days", fields)
        self.assertEqual(fields["subscription_grace_period_days"]["default"], "7")
        self.assertIn(
            "subscription_grace_period_days",
            (ASSISTANT / "settings.py").read_text(encoding="utf-8"),
        )

    def test_commercial_platform_plan_documents_remaining_work(self) -> None:
        source = (ROOT / "docs" / "COMMERCIAL_PLATFORM_IMPLEMENTATION_PLAN.md").read_text(
            encoding="utf-8"
        )

        for phrase in (
            "LLM intent router",
            "Safe CRUD workflow",
            "Voice upgrade",
            "Local/offline package",
            "Cloud package",
            "Subscription enforcement",
            "Not Yet Client Ready",
            "Seven-day subscription grace period",
        ):
            self.assertIn(phrase, source)

    def test_remaining_development_plan_tracks_full_product_gaps(self) -> None:
        source = (ROOT / "docs" / "REMAINING_DEVELOPMENT_PLAN.md").read_text(
            encoding="utf-8"
        )

        for phrase in (
            "Whisper runtime connector",
            "Ollama/Qwen strict intent router",
            "Safe CRUD workflow",
            "Full ERPNext coverage",
            "Urdu/English quality",
            "Subscription and licensing",
            "Backup and restore",
            "Monitoring and support",
            "seven-day grace period",
        ):
            self.assertIn(phrase, source)

    def test_ai_service_deployment_automation_exists(self) -> None:
        for relative_path in (
            ".env.example",
            "docker-compose.ai.yml",
            "docker-compose.ai-local-ports.yml",
            "install-cloud-ai-services.sh",
            "install-local-ai-services.sh",
            "whisper-cpp/Dockerfile",
            "whisper-cpp/entrypoint.sh",
        ):
            self.assertTrue((DEPLOY_AI / relative_path).exists(), relative_path)

    def test_ai_compose_uses_private_services_and_model_bootstrap(self) -> None:
        compose = (DEPLOY_AI / "docker-compose.ai.yml").read_text(encoding="utf-8")
        local_ports = (DEPLOY_AI / "docker-compose.ai-local-ports.yml").read_text(
            encoding="utf-8"
        )
        env = (DEPLOY_AI / ".env.example").read_text(encoding="utf-8")

        self.assertIn("ollama/ollama:latest", compose)
        self.assertIn("ollama pull", compose)
        self.assertIn("OLLAMA_MODEL", compose)
        self.assertIn("WHISPER_MODEL", compose)
        self.assertIn("context: ./deploy/ai/whisper-cpp", compose)
        self.assertIn("expose:", compose)
        self.assertNotIn("0.0.0.0", compose)
        self.assertIn("127.0.0.1:${OLLAMA_PORT:-11434}:11434", local_ports)
        self.assertIn("127.0.0.1:${WHISPER_PORT:-9000}:9000", local_ports)
        self.assertIn("qwen3:8b", env)
        self.assertIn("WHISPER_MODEL=medium", env)

    def test_whisper_container_builds_from_source_and_downloads_model(self) -> None:
        dockerfile = (DEPLOY_AI / "whisper-cpp" / "Dockerfile").read_text(encoding="utf-8")
        entrypoint = (DEPLOY_AI / "whisper-cpp" / "entrypoint.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn("github.com/ggml-org/whisper.cpp", dockerfile)
        self.assertIn("WHISPER_BUILD_SERVER=ON", dockerfile)
        self.assertIn("download-ggml-model.sh", entrypoint)
        self.assertIn("whisper-server", entrypoint)
        self.assertIn("--host 0.0.0.0", entrypoint)

    def test_automated_ai_deployment_documentation_exists(self) -> None:
        source = (ROOT / "docs" / "AUTOMATED_LOCAL_AND_CLOUD_AI_DEPLOYMENT.md").read_text(
            encoding="utf-8"
        )

        for phrase in (
            "Cloud Hosted Mode",
            "Local Offline Mode",
            "qwen3:8b",
            "whisper.cpp",
            "Never expose port `11434`",
            "Never expose port `9000`",
            "Current App Integration Status",
        ):
            self.assertIn(phrase, source)


if __name__ == "__main__":
    unittest.main()

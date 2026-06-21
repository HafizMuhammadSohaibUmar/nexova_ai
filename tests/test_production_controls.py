from __future__ import annotations

import importlib
import sys
import types
import unittest


class FakeCache:
    def __init__(self) -> None:
        self.values: dict[str, int] = {}
        self.expires: dict[str, int] = {}

    def incr(self, key: str) -> int:
        self.values[key] = self.values.get(key, 0) + 1
        return self.values[key]

    def expire(self, key: str, seconds: int) -> None:
        self.expires[key] = seconds


def _install_fake_frappe(cache: FakeCache) -> None:
    fake = types.ModuleType("frappe")
    fake.__path__ = []
    fake.session = types.SimpleNamespace(user="test@example.com")
    fake.local = types.SimpleNamespace(site="test.local")
    fake.flags = types.SimpleNamespace()
    fake.cache = lambda: cache
    fake.throw = lambda message: (_ for _ in ()).throw(Exception(message))
    sys.modules["frappe"] = fake

    fake_utils = types.ModuleType("frappe.utils")
    fake_utils.flt = lambda value=0: float(value or 0)
    fake_utils.getdate = lambda value=None: value
    fake_utils.nowdate = lambda: "2026-06-21"
    sys.modules["frappe.utils"] = fake_utils


class ProductionControlsTest(unittest.TestCase):
    def tearDown(self) -> None:
        sys.modules.pop("frappe", None)
        sys.modules.pop("frappe.utils", None)

    def test_subscription_status_matrix(self) -> None:
        from nexova_ai.assistant.subscription import evaluate_subscription

        self.assertTrue(evaluate_subscription("Active").allowed)

        past_due = evaluate_subscription("Past Due")
        self.assertTrue(past_due.allowed)
        self.assertTrue(past_due.warn_only)
        self.assertEqual(past_due.grace_period_days, 7)
        self.assertIn("7 day", past_due.message)

        in_grace = evaluate_subscription("Past Due", grace_period_days=7, days_past_due=7)
        self.assertTrue(in_grace.allowed)

        after_grace = evaluate_subscription("Past Due", grace_period_days=7, days_past_due=8)
        self.assertFalse(after_grace.allowed)
        self.assertIn("grace period has ended", after_grace.message)

        for status in ("Suspended", "Disabled", "Terminated Pending Retention"):
            with self.subTest(status=status):
                decision = evaluate_subscription(status)
                self.assertFalse(decision.allowed)
                self.assertIn("not active", decision.message)

        self.assertTrue(evaluate_subscription("Suspended", enforcement_enabled=False).allowed)
        self.assertFalse(evaluate_subscription("Unexpected").allowed)

    def test_license_decision_keeps_suspended_sites_readable(self) -> None:
        from nexova_ai.assistant.license import evaluate_license

        active = evaluate_license(
            subscription_status="Active",
            license_mode="Online Subscription",
        )
        self.assertTrue(active.ai_enabled)
        self.assertFalse(active.erp_read_only)

        suspended = evaluate_license(
            subscription_status="Suspended",
            license_mode="Signed Offline License",
        )
        self.assertFalse(suspended.ai_enabled)
        self.assertTrue(suspended.erp_read_only)
        self.assertTrue(suspended.allow_login)
        self.assertTrue(suspended.allow_read)
        self.assertTrue(suspended.allow_backup_export)

        disabled = evaluate_license(
            subscription_status="Suspended",
            license_mode="Disabled",
        )
        self.assertTrue(disabled.ai_enabled)
        self.assertFalse(disabled.erp_read_only)

        expired_grace = evaluate_license(
            subscription_status="Past Due",
            license_mode="Online Subscription",
            grace_period_days=7,
            days_past_due=8,
        )
        self.assertFalse(expired_grace.ai_enabled)
        self.assertTrue(expired_grace.erp_read_only)
        self.assertTrue(expired_grace.allow_backup_export)

    def test_signed_offline_license_accepts_valid_payload_and_rejects_tampering(self) -> None:
        from datetime import date

        from nexova_ai.assistant.license import (
            evaluate_signed_offline_license,
            sign_license_payload,
            verify_license_signature,
        )

        secret = "client-secret"
        payload = {
            "license_key": "INV-TEST",
            "site_id": "test.local",
            "company_id": "client-001",
            "plan": "Local Standard",
            "status": "Active",
            "expires_on": "2026-12-31",
            "grace_period_days": 7,
            "features": ["navigation", "live_data", "voice"],
        }
        signature = sign_license_payload(payload, secret)

        self.assertTrue(verify_license_signature(payload, signature, secret))
        self.assertFalse(
            verify_license_signature({**payload, "status": "Suspended"}, signature, secret)
        )

        decision = evaluate_signed_offline_license(
            payload_json=payload,
            signature=signature,
            verification_secret=secret,
            expected_site_id="test.local",
            today=date(2026, 6, 21),
        )
        self.assertTrue(decision.ai_enabled)
        self.assertFalse(decision.erp_read_only)
        self.assertEqual(decision.license_key, "INV-TEST")

    def test_signed_offline_license_blocks_wrong_site_and_expired_after_grace(self) -> None:
        from datetime import date

        from nexova_ai.assistant.license import evaluate_signed_offline_license, sign_license_payload

        secret = "client-secret"
        payload = {
            "license_key": "INV-TEST",
            "site_id": "test.local",
            "plan": "Local Standard",
            "status": "Active",
            "expires_on": "2026-06-01",
            "grace_period_days": 7,
        }
        signature = sign_license_payload(payload, secret)

        wrong_site = evaluate_signed_offline_license(
            payload_json=payload,
            signature=signature,
            verification_secret=secret,
            expected_site_id="other.local",
            today=date(2026, 6, 2),
        )
        self.assertFalse(wrong_site.ai_enabled)
        self.assertTrue(wrong_site.erp_read_only)
        self.assertIn("different site", wrong_site.message)

        expired = evaluate_signed_offline_license(
            payload_json=payload,
            signature=signature,
            verification_secret=secret,
            expected_site_id="test.local",
            today=date(2026, 6, 21),
        )
        self.assertFalse(expired.ai_enabled)
        self.assertTrue(expired.erp_read_only)
        self.assertTrue(expired.allow_backup_export)

    def test_read_only_guard_blocks_business_writes_when_suspended(self) -> None:
        cache = FakeCache()
        _install_fake_frappe(cache)

        settings_module = importlib.import_module("nexova_ai.assistant.settings")
        read_only = importlib.reload(importlib.import_module("nexova_ai.assistant.read_only"))
        read_only.get_settings = lambda: settings_module.AssistantSettings(
            subscription_status="Suspended",
            subscription_enforcement_enabled=True,
        )

        allowed, message = read_only.is_write_allowed("Sales Invoice", "write")
        self.assertFalse(allowed)
        self.assertIn("readable", message)

        self.assertEqual(read_only.is_write_allowed("Sales Invoice", "read"), (True, ""))
        self.assertEqual(read_only.is_write_allowed("Nexova AI Settings", "write"), (True, ""))

        with self.assertRaises(Exception):
            read_only.enforce_write_allowed(types.SimpleNamespace(doctype="Sales Invoice"), "before_save")

    def test_read_only_guard_skips_migrate_and_patch_operations(self) -> None:
        cache = FakeCache()
        _install_fake_frappe(cache)

        import frappe

        settings_module = importlib.import_module("nexova_ai.assistant.settings")
        read_only = importlib.reload(importlib.import_module("nexova_ai.assistant.read_only"))
        read_only.get_settings = lambda: settings_module.AssistantSettings(
            subscription_status="Suspended",
            subscription_enforcement_enabled=True,
        )

        frappe.flags.in_migrate = True
        read_only.enforce_write_allowed(types.SimpleNamespace(doctype="Sales Invoice"), "before_save")

    def test_rate_limit_allows_until_configured_minute_limit(self) -> None:
        cache = FakeCache()
        _install_fake_frappe(cache)

        settings_module = importlib.import_module("nexova_ai.assistant.settings")
        rate_limit = importlib.reload(importlib.import_module("nexova_ai.assistant.rate_limit"))
        settings = settings_module.AssistantSettings(
            requests_per_minute=2,
            requests_per_day=10,
        )

        self.assertEqual(rate_limit.check_rate_limit(settings), (True, ""))
        self.assertEqual(rate_limit.check_rate_limit(settings), (True, ""))

        allowed, message = rate_limit.check_rate_limit(settings)
        self.assertFalse(allowed)
        self.assertIn("Rate limit", message)

    def test_rate_limit_blocks_daily_limit(self) -> None:
        cache = FakeCache()
        _install_fake_frappe(cache)

        settings_module = importlib.import_module("nexova_ai.assistant.settings")
        rate_limit = importlib.reload(importlib.import_module("nexova_ai.assistant.rate_limit"))
        settings = settings_module.AssistantSettings(
            requests_per_minute=10,
            requests_per_day=1,
        )

        self.assertEqual(rate_limit.check_rate_limit(settings), (True, ""))

        allowed, message = rate_limit.check_rate_limit(settings)
        self.assertFalse(allowed)
        self.assertIn("Daily assistant limit", message)

    def test_rate_limit_can_be_disabled(self) -> None:
        cache = FakeCache()
        _install_fake_frappe(cache)

        settings_module = importlib.import_module("nexova_ai.assistant.settings")
        rate_limit = importlib.reload(importlib.import_module("nexova_ai.assistant.rate_limit"))
        settings = settings_module.AssistantSettings(
            rate_limit_enabled=False,
            requests_per_minute=1,
            requests_per_day=1,
        )

        for _ in range(3):
            self.assertEqual(rate_limit.check_rate_limit(settings), (True, ""))

    def test_vocabulary_normalizes_voice_and_multilingual_phrases(self) -> None:
        from nexova_ai.assistant.intent import detect_intent, detect_language, normalize_text
        from nexova_ai.assistant.vocabulary import contains_phrase, fuzzy_match_score

        self.assertIn("receivables", normalize_text("pending receiveables"))
        self.assertEqual(detect_intent("what are my pending receiveables"), "receivables_summary")
        self.assertEqual(detect_intent("customers dikhao"), "customer_summary")
        self.assertEqual(detect_language("kitne customers hain"), "ur-roman")
        self.assertTrue(contains_phrase("customer list kholo", "navigation"))
        self.assertTrue(contains_phrase("\u06a9\u062a\u0646\u06d2 customers", "count"))
        self.assertLess(
            fuzzy_match_score("customer list kholo", "Sales Invoice List", ("sales invoice",)),
            45,
        )
        self.assertGreaterEqual(
            fuzzy_match_score("customer list kholo", "Customer List", ("customer", "customers")),
            45,
        )

    def test_navigation_prefers_specific_business_terms_over_generic_words(self) -> None:
        cache = FakeCache()
        _install_fake_frappe(cache)

        navigation = importlib.reload(importlib.import_module("nexova_ai.assistant.navigation"))
        navigation.find_specific_document = lambda question: None
        navigation.can_read_doctype = lambda doctype: True

        sales_invoice = navigation.resolve_navigation("sales invoice kholo")
        self.assertEqual(sales_invoice.data["action"], "navigate")
        self.assertEqual(sales_invoice.data["route"], ["List", "Sales Invoice"])

        customer_list = navigation.resolve_navigation("customer list kholo")
        self.assertEqual(customer_list.data["action"], "navigate")
        self.assertEqual(customer_list.data["route"], ["List", "Customer"])

        stock_ledger = navigation.resolve_navigation("stock ledger report open karo")
        self.assertEqual(stock_ledger.data["action"], "navigate")
        self.assertEqual(stock_ledger.data["route"], ["query-report", "Stock Ledger"])

        unpaid_invoices = navigation.resolve_navigation("open sales invoice list and show unpaid invoices")
        self.assertEqual(unpaid_invoices.data["action"], "navigate")
        self.assertEqual(unpaid_invoices.data["route"], ["List", "Sales Invoice"])
        self.assertEqual(unpaid_invoices.data["route_options"]["docstatus"], 1)
        self.assertEqual(unpaid_invoices.data["route_options"]["outstanding_amount"], [">", 0])

    def test_intent_distinguishes_answers_from_explicit_navigation(self) -> None:
        from nexova_ai.assistant.intent import detect_intent

        self.assertEqual(detect_intent("show me top customers by sales"), "customer_wise_sales")
        self.assertEqual(detect_intent("customer list kholo"), "navigation")
        self.assertEqual(detect_intent("stock balance batao"), "stock_balance")

    def test_llm_router_accepts_only_approved_builtin_or_registry_intents(self) -> None:
        cache = FakeCache()
        _install_fake_frappe(cache)

        from nexova_ai.assistant.llm import parse_intent_response

        dynamic = parse_intent_response(
            {"message": {"content": '{"intent":"dynamic_query","confidence":0.91,"arguments":{}}'}}
        )
        self.assertIsNotNone(dynamic)
        self.assertEqual(dynamic.intent, "dynamic_query")

        navigation = parse_intent_response(
            {"message": {"content": '{"intent":"navigation","confidence":0.9,"arguments":{}}'}}
        )
        self.assertIsNotNone(navigation)
        self.assertEqual(navigation.intent, "navigation")

        unsafe = parse_intent_response(
            {"message": {"content": '{"intent":"frappe_db_sql","confidence":1,"arguments":{}}'}}
        )
        self.assertIsNone(unsafe)


if __name__ == "__main__":
    unittest.main()

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
    fake = types.SimpleNamespace()
    fake.session = types.SimpleNamespace(user="test@example.com")
    fake.local = types.SimpleNamespace(site="test.local")
    fake.cache = lambda: cache
    sys.modules["frappe"] = fake


class ProductionControlsTest(unittest.TestCase):
    def tearDown(self) -> None:
        sys.modules.pop("frappe", None)

    def test_subscription_status_matrix(self) -> None:
        from nexova_ai.assistant.subscription import evaluate_subscription

        self.assertTrue(evaluate_subscription("Active").allowed)

        past_due = evaluate_subscription("Past Due")
        self.assertTrue(past_due.allowed)
        self.assertTrue(past_due.warn_only)

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
        from nexova_ai.assistant.vocabulary import contains_phrase

        self.assertIn("receivables", normalize_text("pending receiveables"))
        self.assertEqual(detect_intent("what are my pending receiveables"), "receivables_summary")
        self.assertEqual(detect_intent("customers dikhao"), "customer_summary")
        self.assertEqual(detect_language("kitne customers hain"), "ur-roman")
        self.assertTrue(contains_phrase("customer list kholo", "navigation"))
        self.assertTrue(contains_phrase("\u06a9\u062a\u0646\u06d2 customers", "count"))


if __name__ == "__main__":
    unittest.main()

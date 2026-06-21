from __future__ import annotations

import base64
import hashlib
import hmac
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True)
class LicenseDecision:
    status: str
    ai_enabled: bool
    erp_read_only: bool
    allow_login: bool = True
    allow_read: bool = True
    allow_backup_export: bool = True
    message: str = ""
    license_key: str = ""
    plan: str = ""
    expires_on: str = ""
    days_remaining: int | None = None


@dataclass(frozen=True)
class OfflineLicense:
    license_key: str
    site_id: str
    company_id: str
    plan: str
    status: str
    expires_on: str
    grace_period_days: int
    features: tuple[str, ...] = ()


def evaluate_license(
    *,
    subscription_status: str | None,
    license_mode: str | None,
    enforcement_enabled: bool = True,
    offline_days_remaining: int | None = None,
    grace_period_days: int = 7,
    days_past_due: int | None = None,
) -> LicenseDecision:
    status = subscription_status or "Active"
    mode = license_mode or "Online Subscription"
    grace_days = max(0, int(grace_period_days or 0))

    if not enforcement_enabled or mode == "Disabled":
        return LicenseDecision(status=status, ai_enabled=True, erp_read_only=False)

    if status == "Active":
        return LicenseDecision(status=status, ai_enabled=True, erp_read_only=False)

    if status == "Past Due":
        if days_past_due is not None and days_past_due > grace_days:
            return LicenseDecision(
                status=status,
                ai_enabled=False,
                erp_read_only=True,
                allow_backup_export=True,
                message="Subscription grace period has ended. ERP should remain readable and backup export should remain available.",
            )

        return LicenseDecision(
            status=status,
            ai_enabled=True,
            erp_read_only=False,
            message=f"Subscription is past due. Keep backups current and resolve billing within {grace_days} day(s).",
        )

    if mode == "Signed Offline License" and offline_days_remaining is not None:
        if offline_days_remaining >= 0 and status not in {"Suspended", "Disabled"}:
            return LicenseDecision(status=status, ai_enabled=True, erp_read_only=False)

    if status in {"Suspended", "Disabled", "Terminated Pending Retention"}:
        return LicenseDecision(
            status=status,
            ai_enabled=False,
            erp_read_only=True,
            allow_backup_export=True,
            message="License is not active. ERP should remain readable and backup export should remain available.",
        )

    return LicenseDecision(
        status=status,
        ai_enabled=False,
        erp_read_only=True,
        allow_backup_export=True,
        message="License state is not recognized. ERP should fail closed for writes but keep read and backup access.",
    )


def evaluate_configured_license(settings: Any, today: date | None = None) -> LicenseDecision:
    if getattr(settings, "license_mode", None) == "Signed Offline License":
        return evaluate_signed_offline_license(
            payload_json=getattr(settings, "offline_license_payload", ""),
            signature=getattr(settings, "offline_license_signature", ""),
            verification_secret=getattr(settings, "license_verification_secret", ""),
            expected_site_id=getattr(settings, "site_id", ""),
            enforcement_enabled=getattr(settings, "subscription_enforcement_enabled", True),
            default_grace_period_days=getattr(settings, "subscription_grace_period_days", 7),
            today=today,
        )

    return evaluate_license(
        subscription_status=getattr(settings, "subscription_status", "Active"),
        license_mode=getattr(settings, "license_mode", "Online Subscription"),
        enforcement_enabled=getattr(settings, "subscription_enforcement_enabled", True),
        grace_period_days=getattr(settings, "subscription_grace_period_days", 7),
        days_past_due=_days_past_due(getattr(settings, "past_due_since", None), today=today),
    )


def evaluate_signed_offline_license(
    *,
    payload_json: str | dict[str, Any] | None,
    signature: str | None,
    verification_secret: str | None,
    expected_site_id: str | None = None,
    enforcement_enabled: bool = True,
    default_grace_period_days: int = 7,
    today: date | None = None,
) -> LicenseDecision:
    if not enforcement_enabled:
        return LicenseDecision(status="Active", ai_enabled=True, erp_read_only=False)

    if not verification_secret:
        return _blocked("Missing offline license verification secret.")

    payload = parse_license_payload(payload_json)
    if not payload:
        return _blocked("Missing or invalid signed offline license payload.")

    if not verify_license_signature(payload, signature or "", verification_secret):
        return _blocked("Signed offline license signature is invalid.")

    offline_license = offline_license_from_payload(payload)
    if not offline_license:
        return _blocked("Signed offline license is missing required fields.")

    if expected_site_id and offline_license.site_id != expected_site_id:
        return _blocked("Signed offline license is for a different site.")

    grace_days = offline_license.grace_period_days or int(default_grace_period_days or 7)
    today_value = today or date.today()
    expiry = _parse_date(offline_license.expires_on)
    days_remaining = (expiry - today_value).days if expiry else None
    status = offline_license.status or "Active"

    if expiry and today_value > expiry:
        days_past_due = (today_value - expiry).days
        decision = evaluate_license(
            subscription_status="Past Due",
            license_mode="Signed Offline License",
            enforcement_enabled=True,
            grace_period_days=grace_days,
            days_past_due=days_past_due,
        )
    else:
        decision = evaluate_license(
            subscription_status=status,
            license_mode="Signed Offline License",
            enforcement_enabled=True,
            offline_days_remaining=days_remaining,
            grace_period_days=grace_days,
        )

    return LicenseDecision(
        status=decision.status,
        ai_enabled=decision.ai_enabled,
        erp_read_only=decision.erp_read_only,
        allow_login=decision.allow_login,
        allow_read=decision.allow_read,
        allow_backup_export=decision.allow_backup_export,
        message=decision.message,
        license_key=offline_license.license_key,
        plan=offline_license.plan,
        expires_on=offline_license.expires_on,
        days_remaining=days_remaining,
    )


def parse_license_payload(payload_json: str | dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(payload_json, dict):
        return dict(payload_json)

    if not payload_json:
        return {}

    try:
        parsed = json.loads(payload_json)
    except (TypeError, ValueError):
        return {}

    return parsed if isinstance(parsed, dict) else {}


def offline_license_from_payload(payload: dict[str, Any]) -> OfflineLicense | None:
    license_key = str(payload.get("license_key") or "").strip()
    site_id = str(payload.get("site_id") or "").strip()
    expires_on = str(payload.get("expires_on") or "").strip()
    if not license_key or not site_id or not expires_on:
        return None

    return OfflineLicense(
        license_key=license_key,
        site_id=site_id,
        company_id=str(payload.get("company_id") or "").strip(),
        plan=str(payload.get("plan") or "").strip(),
        status=str(payload.get("status") or "Active").strip() or "Active",
        expires_on=expires_on,
        grace_period_days=_positive_int(payload.get("grace_period_days"), 7),
        features=tuple(str(feature) for feature in payload.get("features") or ()),
    )


def sign_license_payload(payload: dict[str, Any], secret: str) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        _canonical_payload(payload),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def verify_license_signature(payload: dict[str, Any], signature: str, secret: str) -> bool:
    if not payload or not signature or not secret:
        return False

    expected = sign_license_payload(payload, secret)
    return hmac.compare_digest(expected, signature)


def check_license_server(
    *,
    server_url: str,
    license_key: str,
    site_id: str,
    company_id: str = "",
    timeout_seconds: int = 10,
) -> dict[str, Any]:
    url = f"{server_url.rstrip('/')}/api/v1/check"
    body = json.dumps(
        {
            "license_key": license_key,
            "site_id": site_id,
            "company_id": company_id,
        },
        separators=(",", ":"),
    ).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        data = response.read().decode("utf-8")

    parsed = json.loads(data)
    return parsed if isinstance(parsed, dict) else {}


def sync_license_status() -> None:
    import frappe

    from nexova_ai.assistant.settings import get_settings

    settings = get_settings()
    if settings.license_mode != "Online Subscription":
        return

    if not settings.subscription_enforcement_enabled:
        return

    if not settings.license_server_url or not settings.license_key:
        return

    site_id = settings.site_id or getattr(frappe.local, "site", "")

    try:
        result = check_license_server(
            server_url=settings.license_server_url,
            license_key=settings.license_key,
            site_id=site_id,
            company_id=settings.company_id,
        )
    except (OSError, urllib.error.URLError, TimeoutError, ValueError) as exc:
        frappe.log_error(
            title="Invoxia AI License Check Failed",
            message=str(exc),
        )
        return

    _apply_license_result(result)


def _apply_license_result(result: dict[str, Any]) -> None:
    import frappe
    from frappe.utils import now

    doc = frappe.get_single("Nexova AI Settings")
    updates = {
        "subscription_status": result.get("status"),
        "license_plan": result.get("plan"),
        "license_expires_on": result.get("expires_on"),
        "past_due_since": result.get("past_due_since"),
        "subscription_grace_period_days": result.get("grace_period_days"),
        "offline_license_payload": result.get("offline_license_payload"),
        "offline_license_signature": result.get("offline_license_signature"),
        "license_last_checked_on": now(),
    }

    for fieldname, value in updates.items():
        if value not in (None, "") and doc.meta.has_field(fieldname):
            setattr(doc, fieldname, value)

    previous_flag = getattr(frappe.flags, "ignore_nexova_read_only", False)
    frappe.flags.ignore_nexova_read_only = True
    try:
        doc.save(ignore_permissions=True)
        frappe.db.commit()
    finally:
        frappe.flags.ignore_nexova_read_only = previous_flag


def _canonical_payload(payload: dict[str, Any]) -> bytes:
    clean_payload = {key: value for key, value in payload.items() if key != "signature"}
    return json.dumps(
        clean_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _blocked(message: str) -> LicenseDecision:
    return LicenseDecision(
        status="Invalid",
        ai_enabled=False,
        erp_read_only=True,
        allow_backup_export=True,
        message=message,
    )


def _days_past_due(value: Any, today: date | None = None) -> int | None:
    parsed = _parse_date(value)
    if not parsed:
        return None

    return max(0, ((today or date.today()) - parsed).days)


def _parse_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value

    if not value:
        return None

    text = str(value)[:10]
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def _positive_int(value: Any, fallback: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback

    return parsed if parsed > 0 else fallback

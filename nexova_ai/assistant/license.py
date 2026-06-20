from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LicenseDecision:
    status: str
    ai_enabled: bool
    erp_read_only: bool
    allow_login: bool = True
    allow_read: bool = True
    allow_backup_export: bool = True
    message: str = ""


def evaluate_license(
    *,
    subscription_status: str | None,
    license_mode: str | None,
    enforcement_enabled: bool = True,
    offline_days_remaining: int | None = None,
) -> LicenseDecision:
    status = subscription_status or "Active"
    mode = license_mode or "Online Subscription"

    if not enforcement_enabled or mode == "Disabled":
        return LicenseDecision(status=status, ai_enabled=True, erp_read_only=False)

    if status == "Active":
        return LicenseDecision(status=status, ai_enabled=True, erp_read_only=False)

    if status == "Past Due":
        return LicenseDecision(
            status=status,
            ai_enabled=True,
            erp_read_only=False,
            message="Subscription is past due. Keep backups current and resolve billing before grace ends.",
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

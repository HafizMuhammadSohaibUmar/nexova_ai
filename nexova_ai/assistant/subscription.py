from __future__ import annotations

from dataclasses import dataclass


ACTIVE_STATUS = "Active"
PAST_DUE_STATUS = "Past Due"
BLOCKED_STATUSES = {
    "Suspended",
    "Disabled",
    "Terminated Pending Retention",
}


@dataclass(frozen=True)
class SubscriptionDecision:
    allowed: bool
    status: str
    message: str = ""
    warn_only: bool = False
    grace_period_days: int = 7
    days_past_due: int | None = None


def evaluate_subscription(
    status: str | None,
    enforcement_enabled: bool = True,
    *,
    grace_period_days: int = 7,
    days_past_due: int | None = None,
) -> SubscriptionDecision:
    normalized_status = status or ACTIVE_STATUS
    grace_days = max(0, int(grace_period_days or 0))

    if not enforcement_enabled:
        return SubscriptionDecision(
            allowed=True,
            status=normalized_status,
            grace_period_days=grace_days,
            days_past_due=days_past_due,
        )

    if normalized_status == ACTIVE_STATUS:
        return SubscriptionDecision(
            allowed=True,
            status=normalized_status,
            grace_period_days=grace_days,
            days_past_due=days_past_due,
        )

    if normalized_status == PAST_DUE_STATUS:
        if days_past_due is not None and days_past_due > grace_days:
            return SubscriptionDecision(
                allowed=False,
                status=normalized_status,
                message="Invoxia AI subscription grace period has ended. Please renew to continue using the assistant.",
                grace_period_days=grace_days,
                days_past_due=days_past_due,
            )

        return SubscriptionDecision(
            allowed=True,
            status=normalized_status,
            message=f"Invoxia AI subscription is past due. Please update billing within {grace_days} day(s) to avoid suspension.",
            warn_only=True,
            grace_period_days=grace_days,
            days_past_due=days_past_due,
        )

    if normalized_status in BLOCKED_STATUSES:
        return SubscriptionDecision(
            allowed=False,
            status=normalized_status,
            message="Invoxia AI is currently not active for this site.",
            grace_period_days=grace_days,
            days_past_due=days_past_due,
        )

    return SubscriptionDecision(
        allowed=False,
        status=normalized_status,
        message="Invoxia AI subscription status is not recognized. Please contact the administrator.",
        grace_period_days=grace_days,
        days_past_due=days_past_due,
    )

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


def evaluate_subscription(status: str | None, enforcement_enabled: bool = True) -> SubscriptionDecision:
    normalized_status = status or ACTIVE_STATUS

    if not enforcement_enabled:
        return SubscriptionDecision(allowed=True, status=normalized_status)

    if normalized_status == ACTIVE_STATUS:
        return SubscriptionDecision(allowed=True, status=normalized_status)

    if normalized_status == PAST_DUE_STATUS:
        return SubscriptionDecision(
            allowed=True,
            status=normalized_status,
            message="Nexova AI subscription is past due. Please update billing to avoid suspension.",
            warn_only=True,
        )

    if normalized_status in BLOCKED_STATUSES:
        return SubscriptionDecision(
            allowed=False,
            status=normalized_status,
            message="Nexova AI is currently not active for this site.",
        )

    return SubscriptionDecision(
        allowed=False,
        status=normalized_status,
        message="Nexova AI subscription status is not recognized. Please contact the administrator.",
    )

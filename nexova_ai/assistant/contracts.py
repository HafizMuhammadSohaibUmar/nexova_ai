from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class ToolSpec:
    name: str
    label: str
    description: str
    category: str
    required_doctypes: tuple[str, ...]
    risk_level: str
    aliases: tuple[str, ...]
    handler: Callable[[str], dict[str, Any]]


@dataclass(frozen=True)
class NavigationTarget:
    name: str
    label: str
    route: tuple[str, ...]
    category: str
    required_doctype: str | None
    aliases: tuple[str, ...]


@dataclass
class AssistantResult:
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    status: str = "Success"
    intent: str = "unknown"
    tool_name: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "message": self.message,
            "data": self.data,
        }


def response(
    message: str,
    *,
    data: dict[str, Any] | None = None,
    status: str = "Success",
    intent: str = "unknown",
    tool_name: str | None = None,
) -> AssistantResult:
    return AssistantResult(
        message=message,
        data=data or {},
        status=status,
        intent=intent,
        tool_name=tool_name,
    )

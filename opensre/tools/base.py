"""Base tool interface for opensre.

All tools must inherit from BaseTool and implement the required methods
as defined in .cursor/rules/tools.mdc.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolParams:
    """Generic container for tool execution parameters."""

    raw: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.raw.get(key, default)

    def require(self, key: str) -> Any:
        """Return value for *key* or raise KeyError if missing."""
        if key not in self.raw:
            raise KeyError(f"Required parameter '{key}' is missing from tool input")
        return self.raw[key]

    def keys(self) -> list[str]:
        """Return a list of all parameter keys. Handy for debugging."""
        return list(self.raw.keys())


@dataclass
class ToolResult:
    """Standardised result returned by every tool."""

    success: bool
    output: Any = None
    error: str | None = None

    # Convenience constructors ---------------------------------------------------

    @classmethod
    def ok(cls, output: Any = None) -> "ToolResult":
        return cls(success=True, output=output)

    @classmethod
    def fail(cls, error: str) -> "ToolResult":
        return cls(success=False, error=error)


class BaseTool(ABC):
    """Abstract base class every opensre tool must implement.

    Subclasses must provide:
        - ``my_tool_name``  – unique snake_case identifier
        - ``MyToolName``    – human-readable display name (class attribute)
        - ``is_available``  – returns True when the tool can be used in the
                              current environment
        - ``extract_params``– validates / coerces raw input into ToolParams
        - ``run``           – executes the tool and returns a ToolResult
    """

    # ------------------------------------------------------------------ identity

    #: Unique snake_case identifier used for registration and graph references.
    my_tool_name: str = ""

    #: Human-readable display name shown in UIs and log output.
    MyToolName: str = ""

    # ---------------------------------------------------------- lifecycle checks

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this tool's dependencies are satisfied."""

    # ---------------------------------------------------------- parameter layer

    @abstractmethod
    def extract_params(self, raw_input: dict[str, Any]) -> ToolParams:
        """Validate *raw_input* and return a populated ToolParams instance.

        Raise ``ValueError`` with a descriptive message if validation fails.
        """

    # --------------------------------------------------------------- execution

    @abstractmethod
    def run(self, params: ToolParams) -> ToolResult:
        """Execute the tool with the given *params*.

        Should never raise – catch exceptions internally and return
        ``ToolResult.fail(...)`` instead.
        """

    # ------------------------------------------------------------------ helpers

    def safe_run(self, raw_input: dict[str, Any]) -> ToolResult:
        """Convenience method: extract params and run in one call.

        Catches ValueError from extract_params and returns a ToolResult.fail
        so callers don't have to handle the two-step manually.
        """
        try:
            params = self.extract_params(raw_input)
        except (KeyError, ValueError) as exc:
            return ToolResult.fail(f"Parameter error: {exc}")
        return self.run(params)

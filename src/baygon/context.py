"""Manage a minimal Python context for ``{{ ... }}`` templating."""

from __future__ import annotations

import builtins
import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

_DEFAULT_BUILTINS: dict[str, Any] = {
    name: getattr(builtins, name)
    for name in dir(builtins)
    if not name.startswith("_") or name == "__import__"
}
_DEFAULT_BUILTINS.setdefault("__import__", builtins.__import__)


_MUSTACHE_RE = re.compile(r"\{\{\s*(.+?)\s*\}\}", re.DOTALL)
_PRE_INC_RE = re.compile(r"(?<!\+)\+\+\s*([A-Za-z_][A-Za-z0-9_]*)")
_POST_INC_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*\+\+(?!\+)")


class ContextError(RuntimeError):
    """Error raised while using the ``Context``."""

    def __init__(
        self,
        message: str,
        *,
        expression: str | None = None,
        template: str | None = None,
        code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.expression = expression
        self.template = template
        self.code = code


def _split_format_spec(expr: str) -> tuple[str, str | None]:
    """Split ``expr`` into (expression, format_spec) while respecting parentheses."""

    text = expr.strip()
    depth = 0
    in_string = False
    string_char = ""
    escape = False

    for idx, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == string_char:
                in_string = False
            continue
        if ch in "'\"":
            in_string = True
            string_char = ch
            continue
        if ch in "([{":
            depth += 1
            continue
        if ch in ")]}":
            depth = max(depth - 1, 0)
            continue
        if ch == ":" and depth == 0:
            return text[:idx].strip(), text[idx + 1 :].strip() or None
    return text, None


def _rewrite_increments(expr: str) -> str:
    """Replace occurrences of ``x++`` / ``++x`` with Python helpers."""

    def _pre(match: re.Match[str]) -> str:
        return f'_ctx_pre_inc("{match.group(1)}")'

    def _post(match: re.Match[str]) -> str:
        return f'_ctx_post_inc("{match.group(1)}")'

    # Apply pre-increment before post-increment to handle standalone ``++x``
    rewritten = _PRE_INC_RE.sub(_pre, expr)
    rewritten = _POST_INC_RE.sub(_post, rewritten)
    return rewritten


class Context:
    """Small Python environment used by Baygon tests.

    It provides:

    * execution of Python code (`execute`) sharing a local namespace,
    * evaluation of expressions with ``x++`` / ``++x`` support,
    * rendering of strings containing mustaches ``{{ ... }}``.
    """

    def __init__(
        self,
        *,
        builtins_namespace: Mapping[str, Any] | None = None,
        initial: Mapping[str, Any] | None = None,
    ) -> None:
        allowed_builtins = dict(builtins_namespace or _DEFAULT_BUILTINS)
        allowed_builtins.setdefault("__import__", builtins.__import__)

        self._globals: dict[str, Any] = {
            "__builtins__": allowed_builtins,
        }
        self._locals: dict[str, Any] = dict(initial or {})
        self._globals.update({
            "_ctx_pre_inc": self._pre_inc,
            "_ctx_post_inc": self._post_inc,
        })

    # ------------------------------------------------------------------
    # Access helpers
    # ------------------------------------------------------------------

    @property
    def namespace(self) -> Mapping[str, Any]:
        """Return a read-only view of the local namespace."""

        return MappingProxyType(self._locals)

    def __getitem__(self, key: str) -> Any:
        return self._locals[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._locals[key] = value

    # ------------------------------------------------------------------
    # Code / expression handling
    # ------------------------------------------------------------------

    def execute(self, code: str, *, filename: str = "<context>") -> None:
        """Execute Python code within the context namespace."""

        try:
            compiled = compile(code, filename, "exec")
            exec(compiled, self._globals, self._locals)
        except Exception as exc:  # pragma: no cover - formatting only
            raise ContextError(
                "Error while executing context code",
                code=code,
            ) from exc

    def evaluate(self, expression: str) -> Any:
        """Evaluate a Python expression (with ``++`` support)."""

        expr = expression.strip()
        if not expr:
            raise ContextError("Empty expression", expression=expression)

        rewritten = _rewrite_increments(expr)

        try:
            compiled = compile(rewritten, "<context>", "eval")
        except SyntaxError as exc:
            raise ContextError(
                f"Invalid expression: {expression}", expression=expression
            ) from exc

        try:
            return eval(compiled, self._globals, self._locals)
        except Exception as exc:  # pragma: no cover - depends on user code
            raise ContextError(
                f"Error while evaluating '{expression}'",
                expression=expression,
            ) from exc

    # ------------------------------------------------------------------
    # Mustache rendering
    # ------------------------------------------------------------------

    def render(self, template: str) -> str:
        """Replace ``{{ ... }}`` with the evaluated expression."""

        if not isinstance(template, str):
            raise TypeError("template must be a string")

        def _replace(match: re.Match[str]) -> str:
            inner = match.group(1)
            expr, fmt = _split_format_spec(inner)
            value = self.evaluate(expr)
            if fmt:
                return format(value, fmt)
            return str(value)

        try:
            return _MUSTACHE_RE.sub(_replace, template)
        except ContextError as err:
            message = err.message
            if err.expression is not None:
                message = (
                    f"Error while rendering '{{{{ {err.expression} }}}}'"
                )
            raise ContextError(
                message,
                expression=err.expression,
                template=template,
            ) from err.__cause__

    def render_value(self, value: Any) -> Any:
        """Apply ``render`` recursively on str/list/tuple/dict."""

        if isinstance(value, str):
            return self.render(value)
        if isinstance(value, list):
            return [self.render_value(item) for item in value]
        if isinstance(value, tuple):
            return tuple(self.render_value(item) for item in value)
        if isinstance(value, dict):
            return {key: self.render_value(val) for key, val in value.items()}
        return value

    # ------------------------------------------------------------------
    # Increments
    # ------------------------------------------------------------------

    def _pre_inc(self, name: str) -> Any:
        try:
            current = self._locals[name]
        except KeyError as exc:  # pragma: no cover - delegated to evaluate
            raise NameError(name) from exc
        new_value = current + 1
        self._locals[name] = new_value
        return new_value

    def _post_inc(self, name: str) -> Any:
        try:
            current = self._locals[name]
        except KeyError as exc:  # pragma: no cover - delegated to evaluate
            raise NameError(name) from exc
        self._locals[name] = current + 1
        return current


__all__ = ["Context", "ContextError"]


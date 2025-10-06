"""Matcher primitives and registry for Baygon checks."""

from __future__ import annotations

import inspect
import re
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator, MutableMapping, Sequence
from dataclasses import dataclass
from typing import Any, ClassVar

from pydantic import BaseModel, create_model

from .filters import TinyKernel

__all__ = [
    "Matcher",
    "MatcherError",
    "MatcherRegistry",
    "Matchers",
    "MatchEval",
    "MatchRegex",
    "MatchContains",
    "MatchNotContains",
    "MatchEquals",
    "MatchNotEquals",
    "MatchLt",
    "MatchLte",
    "MatchGt",
    "MatchGte",
    "MatchCapture",
    "add_matcher",
    "build_matcher",
    "get_matcher",
    "iter_matchers",
    "registry",
    "matcher_registry",
]


def _camel_to_snake(name: str) -> str:
    parts = []
    for index, char in enumerate(name):
        if char.isupper() and index and (
            not name[index - 1].isupper()
            or (index + 1 < len(name) and name[index + 1].islower())
        ):
            parts.append("_")
        parts.append(char.lower())
    return "".join(parts)


def _normalize_pattern(pattern: str) -> str:
    try:
        return pattern.encode("utf-8").decode("unicode_escape")
    except UnicodeDecodeError:  # pragma: no cover - defensive
        return pattern


@dataclass(slots=True)
class MatcherError:
    """Failure reported by a matcher."""

    value: Any
    expected: Any
    on: str | None = None
    check: str | None = None
    explain: str | None = None
    details: str | None = None

    def _suffix(self) -> str:
        if self.explain:
            return f" ({self.explain})"
        return ""

    def __str__(self) -> str:  # pragma: no cover - overridden by subclasses
        message = self.details or "Matcher failed"
        return f"{message}{self._suffix()}"


class Matcher(ABC):
    """Base matcher interface."""

    registry_name: ClassVar[str | None] = None

    def __init__(self, *, inverse: bool = False, explain: str | None = None) -> None:
        self.inverse = inverse
        self.explain = explain

    @classmethod
    def name(cls) -> str:
        if cls.registry_name:
            return cls.registry_name
        name = cls.__name__
        if name.startswith("Match"):
            name = name[len("Match") :]
        return _camel_to_snake(name)

    @classmethod
    def signature(cls) -> inspect.Signature:
        return inspect.signature(cls.__init__)

    @classmethod
    def schema_model(cls) -> type[BaseModel]:
        fields: dict[str, tuple[Any, Any]] = {}
        signature = cls.signature()
        for name, param in signature.parameters.items():
            if name == "self":
                continue
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                raise TypeError(
                    f"Matcher '{cls.__name__}' exposes variadic parameters which are not supported"
                )
            annotation = param.annotation if param.annotation is not inspect._empty else Any
            default = param.default if param.default is not inspect._empty else ...
            fields[name] = (annotation, default)
        model_name = f"{cls.__name__}Config"
        return create_model(model_name, **fields)  # type: ignore[arg-type]

    def __call__(self, value: Any, **context: Any) -> MatcherError | None:
        success = self._matches(value, **context)
        if self.inverse:
            success = not success
        if success:
            return None
        return self._failure(value, **context)

    @abstractmethod
    def _matches(self, value: Any, **context: Any) -> bool:
        """Return ``True`` if the value satisfies the matcher."""

    @abstractmethod
    def _failure(self, value: Any, **context: Any) -> MatcherError:
        """Return the failure description for ``value``."""


class MatchRegex(Matcher):
    """Regex based matcher."""

    registry_name = "match"

    def __init__(self, regex: str, flags: int | str | None = None, **kwargs: Any) -> None:
        if isinstance(flags, str):
            flag_value = 0
            for char in flags:
                flag_value |= _REGEX_FLAGS.get(char.lower(), 0)
            flags = flag_value or None
        self.pattern = regex
        self.flags = flags
        normalized = _normalize_pattern(regex)
        self.regex = re.compile(normalized, flags or 0)
        super().__init__(**kwargs)

    def _matches(self, value: Any, **context: Any) -> bool:
        string = str(value)
        return self.regex.search(string) is not None

    def _failure(self, value: Any, **context: Any) -> MatcherError:
        on = context.get("on")
        check = context.get("test")
        details = (
            f"Output '{on or 'value'}' does not match /{self.pattern}/"
            f" on {value!r}"
        )
        return MatcherError(value=value, expected=self.pattern, on=on, check=check, explain=self.explain, details=details)


class MatchContains(Matcher):
    def __init__(self, value: str, **kwargs: Any) -> None:
        self.expected = value
        super().__init__(**kwargs)

    def _matches(self, value: Any, **context: Any) -> bool:
        string = str(value)
        return self.expected in string

    def _failure(self, value: Any, **context: Any) -> MatcherError:
        on = context.get("on")
        check = context.get("test")
        message = (
            f"Output {on or 'value'} does not contain {self.expected!r}. "
            f"Found {value!r} instead."
        )
        return MatcherError(value=value, expected=self.expected, on=on, check=check, explain=self.explain, details=message)


class MatchNotContains(MatchContains):
    registry_name = "not_contains"

    def __init__(self, value: str, **kwargs: Any) -> None:
        super().__init__(value=value, inverse=True, **kwargs)

    def _failure(self, value: Any, **context: Any) -> MatcherError:
        on = context.get("on")
        check = context.get("test")
        message = (
            f"Output {on or 'value'} unexpectedly contains {self.expected!r}."
        )
        return MatcherError(value=value, expected=self.expected, on=on, check=check, explain=self.explain, details=message)


class MatchEquals(Matcher):
    def __init__(self, value: str, **kwargs: Any) -> None:
        self.expected = value
        super().__init__(**kwargs)

    def _matches(self, value: Any, **context: Any) -> bool:
        return str(value) == self.expected

    def _failure(self, value: Any, **context: Any) -> MatcherError:
        on = context.get("on")
        check = context.get("test")
        message = (
            f"Output {value!r} does not equal {self.expected!r} on {on or 'value'}."
        )
        return MatcherError(value=value, expected=self.expected, on=on, check=check, explain=self.explain, details=message)


class MatchNotEquals(MatchEquals):
    registry_name = "not_equals"

    def __init__(self, value: str, **kwargs: Any) -> None:
        super().__init__(value=value, inverse=True, **kwargs)

    def _failure(self, value: Any, **context: Any) -> MatcherError:
        on = context.get("on")
        check = context.get("test")
        message = (
            f"Output {on or 'value'} unexpectedly equals {self.expected!r}."
        )
        return MatcherError(value=value, expected=self.expected, on=on, check=check, explain=self.explain, details=message)


class _NumberMatcher(Matcher):
    comparator: ClassVar[str]

    def __init__(self, value: float, **kwargs: Any) -> None:
        self.threshold = float(value)
        self._actual: float | None = None
        self._coerce_error: str | None = None
        super().__init__(**kwargs)

    def _coerce(self, value: Any) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            self._coerce_error = f"cannot convert {value!r} to float"
            self._actual = None
            return None
        self._coerce_error = None
        self._actual = number
        return number

    def _matches(self, value: Any, **context: Any) -> bool:
        number = self._coerce(value)
        if number is None:
            return False
        return self._compare(number)

    @abstractmethod
    def _compare(self, number: float) -> bool:
        ...

    def _failure(self, value: Any, **context: Any) -> MatcherError:
        on = context.get("on")
        check = context.get("test")
        if self._coerce_error:
            message = (
                f"Output {on or 'value'} {self._coerce_error}."
            )
        else:
            message = (
                f"Output {on or 'value'} ({self._actual!r}) is not {self.comparator} {self.threshold!r}."
            )
        return MatcherError(
            value=value,
            expected=self.threshold,
            on=on,
            check=check,
            explain=self.explain,
            details=message,
        )


class MatchLt(_NumberMatcher):
    comparator = "less than"

    def _compare(self, number: float) -> bool:
        return number < self.threshold


class MatchLte(_NumberMatcher):
    comparator = "less than or equal to"

    def _compare(self, number: float) -> bool:
        return number <= self.threshold


class MatchGt(_NumberMatcher):
    comparator = "greater than"

    def _compare(self, number: float) -> bool:
        return number > self.threshold


class MatchGte(_NumberMatcher):
    comparator = "greater than or equal to"

    def _compare(self, number: float) -> bool:
        return number >= self.threshold


class MatchEval(Matcher):
    """Evaluate a Python expression and expect a truthy result."""

    registry_name = "check_eval"

    def __init__(self, expr: str, init: Sequence[str] | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.expr = expr
        self._kernel = TinyKernel()
        for statement in init or []:
            self._kernel(statement)

    def _matches(self, value: Any, **context: Any) -> bool:
        namespace = context.get("namespace") or {}
        self._kernel.glb.update(namespace)
        self._kernel.glb["value"] = value
        self._kernel.glb["actual"] = value
        try:
            self._kernel("_ = " + self.expr)
            result = self._kernel.glb.get("_")
        except SyntaxError:
            result = self._kernel(self.expr)
        return bool(result)

    def _failure(self, value: Any, **context: Any) -> MatcherError:
        on = context.get("on")
        check = context.get("test")
        message = (
            f"Expression {self.expr!r} evaluated to false for {value!r}."
        )
        return MatcherError(value=value, expected=self.expr, on=on, check=check, explain=self.explain, details=message)


class MatchCapture(Matcher):
    """Run nested matchers on a regex capture group."""

    def __init__(
        self,
        regex: str,
        *,
        flags: int | str | None = None,
        group: int = 1,
        tests: Sequence[Matcher] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if isinstance(flags, str):
            flag_value = 0
            for char in flags:
                flag_value |= _REGEX_FLAGS.get(char.lower(), 0)
            flags = flag_value or None
        self.pattern = regex
        self.flags = flags
        normalized = _normalize_pattern(regex)
        self.regex = re.compile(normalized, flags or 0)
        self.group = group
        self.tests = Matchers(tests or [])

    def _matches(self, value: Any, **context: Any) -> bool:
        string = str(value)
        self._captured: str | None = None
        self._nested_failure: MatcherError | None = None
        match = self.regex.search(string)
        if not match:
            return False
        try:
            captured = match.group(self.group)
        except IndexError:
            return False
        self._captured = captured
        nested_context = dict(context)
        base = context.get("on") or "value"
        nested_context["on"] = f"{base}::capture[{self.group}]"
        failures = self.tests.evaluate(captured, **nested_context)
        self._nested_failure = failures[0] if failures else None
        return not failures

    def _failure(self, value: Any, **context: Any) -> MatcherError:
        on = context.get("on")
        check = context.get("test")
        if getattr(self, "_captured", None) is None:
            message = (
                f"Regex capture /{self.pattern}/ failed on {on or 'value'} ({value!r})."
            )
            return MatcherError(
                value=value,
                expected=self.pattern,
                on=on,
                check=check,
                explain=self.explain,
                details=message,
            )
        if getattr(self, "_nested_failure", None):
            failure = self._nested_failure
            message = f"Capture group {self.group} failed nested check: {failure.details or failure}"
            return MatcherError(
                value=self._captured,
                expected=failure.expected,
                on=on,
                check=check,
                explain=self.explain,
                details=message,
            )
        message = (
            f"Capture matcher failed for {on or 'value'} ({value!r})."
        )
        return MatcherError(
            value=value,
            expected=self.pattern,
            on=on,
            check=check,
            explain=self.explain,
            details=message,
        )


class Matchers(Sequence[Matcher]):
    """Ordered collection of matcher instances."""

    def __init__(self, matchers: Iterable[Matcher] | None = None) -> None:
        if matchers is None:
            self._matchers: list[Matcher] = []
        else:
            self._matchers = [self._coerce(item) for item in matchers]

    @staticmethod
    def _coerce(matcher: Matcher) -> Matcher:
        if not isinstance(matcher, Matcher):
            raise TypeError("Matchers collection expects Matcher instances")
        return matcher

    def __iter__(self) -> Iterator[Matcher]:
        return iter(self._matchers)

    def __len__(self) -> int:
        return len(self._matchers)

    def __getitem__(self, index: int) -> Matcher:
        return self._matchers[index]

    def append(self, matcher: Matcher) -> None:
        self._matchers.append(self._coerce(matcher))

    def extend(self, matchers: Iterable[Matcher]) -> None:
        for matcher in matchers:
            self.append(matcher)

    def evaluate(self, value: Any, **context: Any) -> list[MatcherError]:
        failures: list[MatcherError] = []
        for matcher in self._matchers:
            failure = matcher(value, **context)
            if failure is not None:
                failures.append(failure)
        return failures


class MatcherRegistry(MutableMapping[str, type[Matcher]]):
    """Registry of available matcher classes."""

    def __init__(self) -> None:
        self._storage: dict[str, type[Matcher]] = {}

    def __getitem__(self, key: str) -> type[Matcher]:
        return self._storage[key]

    def __setitem__(self, key: str, value: type[Matcher]) -> None:
        self.register(value, name=key)

    def __delitem__(self, key: str) -> None:
        del self._storage[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._storage)

    def __len__(self) -> int:
        return len(self._storage)

    def register(self, matcher_cls: type[Matcher], *, name: str | None = None) -> None:
        if not issubclass(matcher_cls, Matcher):
            raise TypeError("Only Matcher subclasses can be registered")
        key = name or matcher_cls.name()
        if key in self._storage:
            raise TypeError(f"Matcher '{key}' is already registered")
        self._storage[key] = matcher_cls

    def create(self, name: str, /, **kwargs: Any) -> Matcher:
        try:
            matcher_cls = self._storage[name]
        except KeyError as exc:
            raise KeyError(f"Unknown matcher '{name}'") from exc
        return matcher_cls(**kwargs)

    def model(self, name: str) -> type[BaseModel]:
        try:
            matcher_cls = self._storage[name]
        except KeyError as exc:
            raise KeyError(f"Unknown matcher '{name}'") from exc
        return matcher_cls.schema_model()


registry = MatcherRegistry()
matcher_registry = registry


def add_matcher(name: str, matcher_cls: type[Matcher] | None = None):
    """Register a matcher in the global registry."""

    if matcher_cls is None:
        if isinstance(name, type) and issubclass(name, Matcher):  # type: ignore[arg-type]
            matcher_cls = name  # type: ignore[assignment]
            name = matcher_cls.name()
        else:  # pragma: no cover - defensive
            raise TypeError("matcher_cls must be provided when name is not a Matcher subclass")
    registry.register(matcher_cls, name=name)
    return matcher_cls


def get_matcher(name: str) -> type[Matcher]:
    return registry[name]


def iter_matchers() -> Iterator[tuple[str, type[Matcher]]]:
    yield from registry.items()


def build_matcher(check: Any) -> Matcher:
    """Create a matcher instance from a :class:`~baygon.schema.CheckBase`."""

    from .schema import CheckBase, parse_check

    if isinstance(check, CheckBase):
        kind = check.kind
        payload = check.model_dump(exclude={"kind"})
    elif isinstance(check, dict) and "kind" in check:
        kind = check["kind"]
        payload = {k: v for k, v in check.items() if k != "kind"}
    else:
        return build_matcher(parse_check(check))
    tests = payload.pop("tests", None)
    if tests is not None:
        payload["tests"] = [build_matcher(item) for item in tests]
    return registry.create(kind, **payload)


_REGEX_FLAGS: dict[str, int] = {
    "i": re.IGNORECASE,
    "m": re.MULTILINE,
    "s": re.DOTALL,
    "x": re.VERBOSE,
}


for builtin in (
    MatchRegex,
    MatchContains,
    MatchNotContains,
    MatchEquals,
    MatchNotEquals,
    MatchLt,
    MatchLte,
    MatchGt,
    MatchGte,
    MatchEval,
    MatchCapture,
):
    registry.register(builtin)


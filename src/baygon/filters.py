"""Filter primitives and registry for Baygon."""

from __future__ import annotations

import inspect
import re
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator, MutableMapping, Sequence
from typing import Any, ClassVar

from pydantic import BaseModel, create_model

from tinykernel import TinyKernel

__all__ = [
    "Filter",
    "FilterError",
    "FilterRegistry",
    "Filters",
    "add_filter",
    "get_filter",
    "iter_filters",
    "registry",
    # Builtins
    "FilterNone",
    "FilterUppercase",
    "FilterLowercase",
    "FilterTrim",
    "FilterIgnoreSpaces",
    "FilterReplace",
    "FilterRegex",
    "FilterEval",
]


def _camel_to_snake(name: str) -> str:
    parts = []
    for index, char in enumerate(name):
        if char.isupper() and index and (
            not name[index - 1].isupper() or (index + 1 < len(name) and name[index + 1].islower())
        ):
            parts.append("_")
        parts.append(char.lower())
    return "".join(parts)


class FilterError(RuntimeError):
    """Base error type for filter related issues."""


class Filter(ABC):
    """Minimal interface implemented by all filters."""

    #: Optional explicit registry name.
    registry_name: ClassVar[str | None] = None

    def __init__(self, *, input: bool = False) -> None:
        self.input = input

    @abstractmethod
    def apply(self, value: str) -> str:
        """Transform ``value`` and return the result."""

    def filter(self, value: str) -> str:
        return self.apply(value)

    def __call__(self, value: str) -> str:  # pragma: no cover - convenience
        return self.filter(value)

    @classmethod
    def name(cls) -> str:
        """Return the canonical registry name for the filter class."""

        if cls.registry_name:
            return cls.registry_name
        name = cls.__name__
        if name.startswith("Filter"):
            name = name[len("Filter") :]
        return _camel_to_snake(name)

    @classmethod
    def signature(cls) -> inspect.Signature:
        """Return the ``__init__`` signature for the filter."""

        return inspect.signature(cls.__init__)

    @classmethod
    def schema_model(cls) -> type[BaseModel]:
        """Return a Pydantic model mirroring the filter constructor."""

        fields: dict[str, tuple[Any, Any]] = {}
        signature = cls.signature()
        for name, param in signature.parameters.items():
            if name == "self":
                continue
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                raise FilterError(
                    f"Filter '{cls.__name__}' exposes variadic parameters which are not supported"
                )
            annotation = param.annotation if param.annotation is not inspect._empty else Any
            default = param.default if param.default is not inspect._empty else ...
            fields[name] = (annotation, default)
        model_name = f"{cls.__name__}Config"
        return create_model(model_name, **fields)  # type: ignore[arg-type]


class Filters(Sequence[Filter]):
    """Ordered collection of filters."""

    def __init__(self, filters: Iterable[Filter] | None = None) -> None:
        if filters is None:
            self._filters: list[Filter] = []
        else:
            self._filters = [self._coerce(item) for item in filters]

    @staticmethod
    def _coerce(filter_: Filter) -> Filter:
        if not isinstance(filter_, Filter):
            raise TypeError("Filters collection expects Filter instances")
        return filter_

    def __iter__(self) -> Iterator[Filter]:
        return iter(self._filters)

    def __len__(self) -> int:
        return len(self._filters)

    def __getitem__(self, index: int) -> Filter:
        return self._filters[index]

    def append(self, filter_: Filter) -> None:
        self._filters.append(self._coerce(filter_))

    def extend(self, filters: Iterable[Filter]) -> None:
        for filter_ in filters:
            self.append(filter_)

    def apply(self, value: str) -> str:
        for filter_ in self._filters:
            value = filter_.filter(value)
        return value


class FilterRegistry(MutableMapping[str, type[Filter]]):
    """Registry of available filter classes."""

    def __init__(self) -> None:
        self._storage: dict[str, type[Filter]] = {}

    def __getitem__(self, key: str) -> type[Filter]:
        return self._storage[key]

    def __setitem__(self, key: str, value: type[Filter]) -> None:
        self.register(value, name=key)

    def __delitem__(self, key: str) -> None:
        del self._storage[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._storage)

    def __len__(self) -> int:
        return len(self._storage)

    def register(self, filter_cls: type[Filter], *, name: str | None = None) -> None:
        if not issubclass(filter_cls, Filter):
            raise TypeError("Only Filter subclasses can be registered")
        key = name or filter_cls.name()
        if key in self._storage:
            raise FilterError(f"Filter '{key}' is already registered")
        self._storage[key] = filter_cls

    def get(self, name: str) -> type[Filter]:  # pragma: no cover - alias for mapping get
        return self._storage[name]

    def create(self, name: str, /, **kwargs: Any) -> Filter:
        try:
            filter_cls = self._storage[name]
        except KeyError as exc:  # pragma: no cover - defensive
            raise FilterError(f"Unknown filter '{name}'") from exc
        return filter_cls(**kwargs)

    def model(self, name: str) -> type[BaseModel]:
        try:
            filter_cls = self._storage[name]
        except KeyError as exc:  # pragma: no cover - defensive
            raise FilterError(f"Unknown filter '{name}'") from exc
        return filter_cls.schema_model()


registry = FilterRegistry()


def add_filter(name: str, filter_cls: type[Filter] | None = None):
    """Register a new filter in the global registry."""

    if filter_cls is None:
        if isinstance(name, type) and issubclass(name, Filter):  # type: ignore[arg-type]
            filter_cls = name  # type: ignore[assignment]
            name = filter_cls.name()
        else:  # pragma: no cover - defensive fallback
            raise TypeError("filter_cls must be provided when name is not a Filter subclass")
    registry.register(filter_cls, name=name)
    return filter_cls


def get_filter(name: str) -> type[Filter]:
    return registry[name]


def iter_filters() -> Iterator[tuple[str, type[Filter]]]:
    for item in registry.items():
        yield item


# ---------------------------------------------------------------------------
# Builtin filters
# ---------------------------------------------------------------------------


class FilterNone(Filter):
    def apply(self, value: str) -> str:
        return value


class FilterUppercase(Filter):
    def apply(self, value: str) -> str:
        return value.upper()


class FilterLowercase(Filter):
    def apply(self, value: str) -> str:
        return value.lower()


class FilterTrim(Filter):
    def apply(self, value: str) -> str:
        return value.strip()


class FilterIgnoreSpaces(Filter):
    def apply(self, value: str) -> str:
        return value.replace(" ", "")


class FilterReplace(Filter):
    def __init__(self, pattern: str, replacement: str, *, input: bool = False) -> None:
        super().__init__(input=input)
        self.pattern = pattern
        self.replacement = replacement

    def apply(self, value: str) -> str:
        return value.replace(self.pattern, self.replacement)


class FilterRegex(Filter):
    def __init__(self, pattern: str, replacement: str, flags: int | str | None = None, *, input: bool = False) -> None:
        super().__init__(input=input)
        if isinstance(flags, str):
            flag_value = 0
            for char in flags:
                flag_value |= _REGEX_FLAGS.get(char.lower(), 0)
            flags = flag_value or None
        self.pattern = pattern
        self.replacement = replacement
        self.flags = flags
        self.regex = re.compile(pattern, flags or 0)

    def apply(self, value: str) -> str:
        return self.regex.sub(self.replacement, value)


class FilterEval(Filter):
    def __init__(
        self,
        start: str = "{{",
        end: str = "}}",
        init: Sequence[str] | None = None,
        *,
        input: bool = False,
    ) -> None:
        super().__init__(input=input)
        self._mustache = re.compile(f"{re.escape(start)}(.*?){re.escape(end)}")
        self._kernel = TinyKernel()
        bootstrap = list(init or []) + [
            "from math import *",
            "from random import *",
            "from statistics import *",
            "from baygon.eval import iter",
        ]
        for statement in bootstrap:
            self._kernel(statement)

    def apply(self, value: str) -> str:
        position = 0
        result = []
        for match in self._mustache.finditer(value):
            result.append(value[position : match.start()])
            result.append(str(self.exec(match.group(1))))
            position = match.end()
        result.append(value[position:])
        return "".join(result)

    def exec(self, code: str) -> Any:
        code = re.sub(r"((?<=\b)iter\(.*?)(\))", fr"\1,ctx={hash(code)}\2", code)
        try:
            self._kernel("_ = " + code)
            return self._kernel.glb["_"]
        except SyntaxError:
            return self._kernel(code)

    def __repr__(self) -> str:  # pragma: no cover - repr helper
        return f"{self.__class__.__name__}({self._mustache.pattern!r})"


# Flag mapping for FilterRegex string flags -> re flags
_REGEX_FLAGS: dict[str, int] = {
    "i": re.IGNORECASE,
    "m": re.MULTILINE,
    "s": re.DOTALL,
    "x": re.VERBOSE,
}


# Register builtins
for builtin in (
    FilterNone,
    FilterUppercase,
    FilterLowercase,
    FilterTrim,
    FilterIgnoreSpaces,
    FilterReplace,
    FilterRegex,
    FilterEval,
):
    registry.register(builtin)

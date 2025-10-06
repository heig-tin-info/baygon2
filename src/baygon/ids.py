"""Utilities to handle hierarchical test identifiers.

The :class:`TestId` class behaves like an immutable sequence of integers and makes it easy to
traverse a hierarchy of test groups while keeping human friendly numbering (``1.2.3``). The
companion :class:`TrackId` helper offers a small stateful wrapper used by the reporting pipeline to
mutate the current identifier as we enter/leave nested groups of tests.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator, Sequence
from typing import Any, Callable

_VALID_ID = re.compile(r"\d+(?:\.\d+)*$")


class TestId(Sequence[int]):
    __test__ = False
    """Immutable hierarchical identifier.

    ``TestId`` exposes a ``Sequence`` interface which means it can be iterated over or converted to
    other container types (``tuple(id)`` or ``list(id)``). A handful of convenience helpers make it
    straightforward to walk up and down a tree of tests while keeping a predictable numbering
    scheme. Instances are immutable; any operation returns a new ``TestId``.
    """

    __slots__ = ("_parts",)

    def __init__(self, value: Iterable[int] | int | str | TestId | None = None) -> None:
        parts: tuple[int, ...]

        if value is None:
            parts = (1,)
        elif isinstance(value, TestId):
            parts = value._parts
        elif isinstance(value, int):
            parts = (value,)
        elif isinstance(value, str):
            if not _VALID_ID.fullmatch(value):
                raise ValueError(f"Invalid identifier string: {value!r}")
            parts = tuple(int(chunk) for chunk in value.split("."))
        else:
            try:
                parts = tuple(int(chunk) for chunk in value)  # type: ignore[arg-type]
            except TypeError as exc:  # pragma: no cover - defensive guard
                raise TypeError(f"Unsupported identifier type: {type(value)!r}") from exc

        if not parts:
            raise ValueError("A TestId cannot be empty")

        for chunk in parts:
            if not isinstance(chunk, int):  # pragma: no cover - defensive guard
                raise TypeError("Identifier parts must be integers")
            if chunk < 1:
                raise ValueError("Identifier parts must be positive integers")

        self._parts = parts

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------

    def next(self, step: int = 1) -> TestId:
        """Return a new identifier with the last component incremented."""

        if not isinstance(step, int):
            raise TypeError("step must be an integer")
        if step < 1:
            raise ValueError("step must be a positive integer")
        parts = (*self._parts[:-1], self._parts[-1] + step)
        return TestId(parts)

    def down(self, start: int = 1) -> TestId:
        """Return a new identifier nested one level deeper."""

        if not isinstance(start, int):
            raise TypeError("start must be an integer")
        if start < 1:
            raise ValueError("start must be a positive integer")
        return TestId((*self._parts, start))

    def up(self) -> TestId:
        """Return the parent identifier (or itself if already at the root)."""

        if len(self._parts) == 1:
            return self
        return TestId(self._parts[:-1])

    # ------------------------------------------------------------------
    # Sequence protocol
    # ------------------------------------------------------------------

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._parts)

    def __iter__(self) -> Iterator[int]:  # pragma: no cover - trivial
        return iter(self._parts)

    def __getitem__(self, item: int | slice) -> int | Sequence[int]:  # pragma: no cover - trivial
        return self._parts[item]

    # ------------------------------------------------------------------
    # Formatting & comparison helpers
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        return ".".join(str(part) for part in self._parts)

    def __repr__(self) -> str:  # pragma: no cover - repr is simple
        return f"TestId({str(self)})"

    def __hash__(self) -> int:  # pragma: no cover - tuple hashing
        return hash(self._parts)

    def __eq__(self, other: object) -> bool:  # pragma: no cover - trivial
        if isinstance(other, TestId):
            return self._parts == other._parts
        if isinstance(other, Sequence):
            return tuple(self._parts) == tuple(other)
        return NotImplemented

    def __add__(self, value: int) -> TestId:
        """Alias for :meth:`next` so ``id + 1`` works naturally."""

        return self.next(value)

    def pad(self, fill: str = "  ") -> str:
        """Return indentation useful when rendering a hierarchical list."""

        if not isinstance(fill, str):  # pragma: no cover - defensive guard
            raise TypeError("fill must be a string")
        return fill * (len(self) - 1)

    @property
    def parts(self) -> tuple[int, ...]:  # pragma: no cover - simple accessor
        return self._parts


class TrackId:
    """Stateful helper keeping track of the current test identifier."""

    __slots__ = ("_current", "_last", "_stack")

    def __init__(self, start: TestId | Iterable[int] | int | str | None = None) -> None:
        self._current = TestId(start)
        self._last: TestId | None = None
        self._stack: list[tuple[TestId, TestId | None]] = []

    @property
    def current(self) -> TestId:
        """Return the current identifier."""

        return self._current

    def reset(self, value: TestId | Iterable[int] | int | str | None = None) -> Callable[[Any], Any]:
        """Return a callback that resets the tracker to ``value`` (default: ``TestId()``)."""

        def _reset(payload: Any = None) -> Any:
            self._current = TestId(value)
            self._last = None
            self._stack.clear()
            return payload

        return _reset

    def down(self, start: int = 1) -> Callable[[Any], Any]:
        """Return a callback entering a nested group."""

        def _down(payload: Any = None) -> Any:
            base = self._last if self._last is not None else self._current
            self._stack.append((self._current, self._last))
            self._current = base.down(start)
            self._last = None
            return payload

        return _down

    def up(self) -> Callable[[Any], Any]:
        """Return a callback leaving the current group."""

        def _up(payload: Any = None) -> Any:
            if self._stack:
                self._current, self._last = self._stack.pop()
            else:
                self._current = self._current.up()
                self._last = None
            return payload

        return _up

    def next(self, step: int = 1) -> Callable[[dict[str, Any]], dict[str, Any]]:
        """Return a callback that assigns the identifier to a payload and increments it."""

        def _next(payload: dict[str, Any]) -> dict[str, Any]:
            payload["test_id"] = list(self._current)
            self._last = self._current
            self._current = self._current.next(step)
            return payload

        return _next


__all__ = ["TestId", "TrackId"]


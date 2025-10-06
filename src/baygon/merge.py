"""Utility propagation of inheritable ``Spec`` fields."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from typing import Any

from pydantic import BaseModel

from .schema import TESTCASE_PROPAGATION, FileSpec, Spec, TestCase


def _clone_items(items: list[Any]) -> list[Any]:
    """Return a cloned list (``model_copy`` for Pydantic models)."""

    cloned: list[Any] = []
    for item in items:
        if isinstance(item, BaseModel):
            cloned.append(item.model_copy(deep=True))
        else:
            cloned.append(deepcopy(item))
    return cloned


def _merge_files(
    parent: dict[str, FileSpec],
    child: dict[str, FileSpec],
) -> dict[str, FileSpec]:
    """Merge file expectations while preserving parent → child order."""

    merged: dict[str, FileSpec] = {
        name: spec.model_copy(deep=True) for name, spec in parent.items()
    }

    for name, spec in child.items():
        if name in merged:
            merged[name].ops.extend(_clone_items(list(spec.ops)))
        else:
            merged[name] = spec.model_copy(deep=True)

    return merged


FieldInitializer = Callable[[Spec], Any]


_FIELD_INITIALIZERS: dict[str, FieldInitializer] = {
    "filters": lambda spec: list(spec.filters),
    "setup": lambda spec: [],
    "teardown": lambda spec: [],
    "args": lambda spec: list(spec.exec.args),
    "stdin": lambda spec: spec.exec.stdin,
    "files": lambda spec: {},
    "timeout": lambda spec: spec.timeout,
    "ulimit": lambda spec: dict(spec.ulimit) if spec.ulimit is not None else None,
}

_expected = set(TESTCASE_PROPAGATION)
_initial_keys = set(_FIELD_INITIALIZERS)
_missing = _expected - _initial_keys
_extra = _initial_keys - _expected
if _missing or _extra:  # pragma: no cover - configuration guard
    raise RuntimeError(
        "Inconsistent propagation configuration",
        {"missing": sorted(_missing), "extra": sorted(_extra)},
    )


def _combine_field(mode: str, parent: Any, child: Any) -> Any:
    if mode == "list_parent_first":
        return [*(parent or []), *(child or [])]
    if mode == "list_child_first":
        return [*(child or []), *(parent or [])]
    if mode == "fallback":
        return child if child is not None else parent
    if mode == "files":
        return _merge_files(parent or {}, child or {})
    if mode == "dict_merge":
        if child is None:
            if parent is None:
                return None
            return dict(parent)
        merged: dict[str, int] = dict(parent or {})
        merged.update(child)
        return merged
    raise ValueError(f"Unknown propagation mode: {mode}")


def _assign_field(mode: str, meta: dict[str, Any], value: Any) -> Any:
    if mode.startswith("list"):
        items = list(value)
        if meta.get("clone"):
            return _clone_items(items)
        return items
    if mode == "dict_merge":
        return None if value is None else dict(value)
    if mode == "files":
        return value
    if mode == "fallback" and isinstance(value, list):
        return list(value)
    return value


def _context_value(mode: str, value: Any) -> Any:
    if mode.startswith("list"):
        return list(value)
    if mode == "dict_merge":
        return None if value is None else dict(value)
    if mode == "files":
        return value
    if mode == "fallback" and isinstance(value, list):
        return list(value)
    return value


def _initial_context(spec: Spec) -> dict[str, Any]:
    ctx: dict[str, Any] = {}
    for name, initializer in _FIELD_INITIALIZERS.items():
        ctx[name] = initializer(spec)
    return ctx


def _propagate(test: TestCase, ctx: dict[str, Any]) -> None:
    child_ctx: dict[str, Any] = {}
    for name, meta in TESTCASE_PROPAGATION.items():
        mode = meta["mode"]
        parent_value = ctx.get(name)
        local_value = getattr(test, name)
        combined = _combine_field(mode, parent_value, local_value)
        setattr(test, name, _assign_field(mode, meta, combined))
        child_ctx[name] = _context_value(mode, combined)

    if test.tests:
        for child in test.tests:
            _propagate(child, child_ctx)


def merge_spec(spec: Spec) -> Spec:
    """Return a copy of ``spec`` with inheritable fields propagated."""

    merged = spec.model_copy(deep=True)

    base_ctx = _initial_context(merged)

    for test in merged.tests:
        _propagate(test, base_ctx)

    return merged


__all__ = ["merge_spec"]

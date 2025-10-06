"""Propagation utilitaire des champs héritables d'un ``Spec``."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from pydantic import BaseModel

from .schema import FileSpec, Spec, TestCase


def _clone_items(items: list[Any]) -> list[Any]:
    """Retourne une liste clonée (``model_copy`` pour les objets Pydantic)."""

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
    """Fusionne les attentes sur les fichiers en préservant l'ordre parent → enfant."""

    merged: dict[str, FileSpec] = {
        name: spec.model_copy(deep=True) for name, spec in parent.items()
    }

    for name, spec in child.items():
        if name in merged:
            merged[name].ops.extend(_clone_items(list(spec.ops)))
        else:
            merged[name] = spec.model_copy(deep=True)

    return merged


def _propagate(test: TestCase, ctx: dict[str, Any]) -> None:
    local_filters = list(test.filters)
    combined_filters = [*ctx["filters"], *local_filters]
    test.filters = _clone_items(combined_filters)

    local_setup = list(test.setup)
    combined_setup = [*ctx["setup"], *local_setup]
    test.setup = _clone_items(combined_setup)

    local_teardown = list(test.teardown)
    combined_teardown = [*local_teardown, *ctx["teardown"]]
    test.teardown = _clone_items(combined_teardown)

    local_args = list(test.args)
    combined_args = [*ctx["args"], *local_args]
    test.args = list(combined_args)

    test.stdin = test.stdin if test.stdin is not None else ctx["stdin"]

    test.files = _merge_files(ctx["files"], test.files)

    child_ctx = {
        "filters": combined_filters,
        "setup": combined_setup,
        "teardown": combined_teardown,
        "args": combined_args,
        "stdin": test.stdin,
        "files": test.files,
    }

    if test.tests:
        for child in test.tests:
            _propagate(child, child_ctx)


def merge_spec(spec: Spec) -> Spec:
    """Retourne une copie de ``spec`` avec propagation des champs héritables."""

    merged = spec.model_copy(deep=True)

    base_ctx = {
        "filters": list(merged.filters),
        "setup": [],
        "teardown": [],
        "args": list(merged.exec.args),
        "stdin": merged.exec.stdin,
        "files": {},
    }

    for test in merged.tests:
        _propagate(test, base_ctx)

    return merged


__all__ = ["merge_spec"]

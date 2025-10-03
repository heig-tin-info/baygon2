"""Utilities to propagate inherited configuration to nested tests.

Le schéma normalisé (`schema.py`) permet d'exprimer une configuration très
compacte : des filtres ou des étapes de setup peuvent être définis à un niveau
supérieur et s'appliquent implicitement aux tests enfants.  Pour exécuter les
tests il est plus pratique de disposer d'une vue *mergeée* où chaque test
contient explicitement tout ce qui lui est applicable.

Ce module effectue cette propagation en respectant les règles suivantes :

* Les listes (`filters`, `stdout`, `stderr`, `files.*.ops`, `setup`,
  `teardown`) sont concaténées en préservant l'ordre : ce qui est défini en
  amont apparaît avant (ou après pour `teardown`).
* Les valeurs scalaires (`stdin`, `exit`) se comportent comme des valeurs par
  défaut qui peuvent être redéfinies plus bas.
* Les listes d'arguments (`args`) s'empilent : on obtient la somme des arguments
  hérités et locaux.
* `repeat` est multiplicatif, ce qui permet d'exprimer « répéter toute cette
  suite N fois » puis « répéter ce test M fois ».

Le module travaille sur les objets Pydantic normalisés afin de conserver la
validation réalisée dans `schema.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, MutableMapping

from pydantic import BaseModel

from .schema import FileSpec, Spec, TestCase

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clone_models(seq: Iterable[BaseModel]) -> list[BaseModel]:
    """Return deep copies of Pydantic models contained in ``seq``."""

    return [item.model_copy(deep=True) for item in seq]


def _merge_file_specs(
    parent: Mapping[str, Iterable[BaseModel]],
    local: MutableMapping[str, FileSpec],
) -> dict[str, FileSpec]:
    """Combine inherited and local file expectations.

    The operations defined higher in the tree are prepended to the local ones.
    Files that only exist upstream are still present downstream.
    """

    merged: dict[str, FileSpec] = {}

    for name, inherited_ops in parent.items():
        child = local.get(name)
        if child is None:
            merged[name] = FileSpec(ops=_clone_models(inherited_ops))
            continue
        ops = [*inherited_ops, *child.ops]
        merged[name] = FileSpec(ops=_clone_models(ops))

    for name, spec in local.items():
        if name not in merged:
            merged[name] = FileSpec(ops=_clone_models(spec.ops))

    return merged


@dataclass(slots=True)
class _Context:
    filters: tuple[BaseModel, ...]
    stdout: tuple[BaseModel, ...]
    stderr: tuple[BaseModel, ...]
    files: dict[str, tuple[BaseModel, ...]]
    setup: tuple[BaseModel, ...]
    teardown: tuple[BaseModel, ...]
    stdin: str | list[str] | None
    args: tuple[str, ...]
    exit: int | None
    repeat: int


def _merge_testcase(test: TestCase, ctx: _Context) -> TestCase:
    """Return a copy of ``test`` enriched with inherited configuration."""

    copy = test.model_copy(deep=True)

    # Filters
    local_filters = list(copy.filters)
    merged_filters = [*ctx.filters, *local_filters]
    copy.filters = _clone_models(merged_filters)

    # Stream operations (stdout/stderr)
    merged_stdout = [*ctx.stdout, *copy.stdout]
    copy.stdout = _clone_models(merged_stdout)

    merged_stderr = [*ctx.stderr, *copy.stderr]
    copy.stderr = _clone_models(merged_stderr)

    # Files expectations
    merged_files = _merge_file_specs(ctx.files, copy.files)
    copy.files = merged_files

    # Setup/teardown inheritence
    merged_setup = [*ctx.setup, *copy.setup]
    copy.setup = _clone_models(merged_setup)

    merged_teardown = [*copy.teardown, *ctx.teardown]
    copy.teardown = _clone_models(merged_teardown)

    # Arguments: inherited ones first
    merged_args = [*ctx.args, *copy.args]
    copy.args = list(merged_args)

    # stdin / exit behave as defaults
    copy.stdin = copy.stdin if copy.stdin is not None else ctx.stdin
    copy.exit = copy.exit if copy.exit is not None else ctx.exit

    # repeat is multiplicative (suite repeat applies to nested tests)
    copy.repeat = ctx.repeat * copy.repeat

    if copy.tests:
        child_ctx = _Context(
            filters=tuple(merged_filters),
            stdout=tuple(merged_stdout),
            stderr=tuple(merged_stderr),
            files={name: tuple(spec.ops) for name, spec in merged_files.items()},
            setup=tuple(merged_setup),
            teardown=tuple(merged_teardown),
            stdin=copy.stdin,
            args=tuple(merged_args),
            exit=copy.exit,
            repeat=copy.repeat,
        )
        copy.tests = [_merge_testcase(child, child_ctx) for child in copy.tests]

    return copy


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def merge_spec(spec: Spec) -> Spec:
    """Return a new :class:`Spec` where inherited fields are propagated."""

    merged = spec.model_copy(deep=True)

    base_ctx = _Context(
        filters=tuple(merged.filters),
        stdout=(),
        stderr=(),
        files={},
        setup=(),
        teardown=(),
        stdin=merged.exec.stdin,
        args=tuple(merged.exec.args),
        exit=None,
        repeat=1,
    )

    merged.tests = [_merge_testcase(test, base_ctx) for test in merged.tests]

    return merged


__all__ = ["merge_spec"]


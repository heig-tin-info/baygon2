"""Chargement agnostique YAML/JSON avec gestion des erreurs de syntaxe.

Ce module fournit une couche d'I/O minimale pour la DSL "baygon". Il
permet de charger un texte ou un fichier et de le convertir en objet
Python en essayant successivement les parseurs JSON et YAML. Les erreurs
de syntaxe sont collectées pour qu'une CLI puisse les afficher de manière
pédagogique.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from yaml import YAMLError, safe_load

Format = Literal["auto", "json", "yaml"]


@dataclass(slots=True)
class SyntaxIssue:
    """Description d'une erreur de syntaxe détectée par un parseur."""

    parser: Literal["json", "yaml"]
    message: str
    source: str | None = None
    line: int | None = None
    column: int | None = None
    hint: str | None = None

    def format_location(self) -> str:
        source = self.source or "<string>"
        if self.line is None:
            return source
        if self.column is None:
            return f"{source}:{self.line}"
        return f"{source}:{self.line}:{self.column}"

    def to_message(self) -> str:
        location = self.format_location()
        if self.hint:
            return f"[{self.parser}] {location}: {self.message} ({self.hint})"
        return f"[{self.parser}] {location}: {self.message}"


class ConfigSyntaxError(Exception):
    """Erreur levée lorsque la configuration est invalide syntaxiquement."""

    def __init__(self, issues: Iterable[SyntaxIssue]):
        self.issues = list(issues)
        if not self.issues:
            raise ValueError("ConfigSyntaxError requiert au moins une erreur")
        super().__init__("\n".join(issue.to_message() for issue in self.issues))


def _format_json_issue(source: str | None, err: json.JSONDecodeError) -> SyntaxIssue:
    hint = None
    message = err.msg
    if "Expecting property name" in err.msg:
        hint = "Les clés JSON doivent être entourées de guillemets doubles"
    return SyntaxIssue(
        parser="json",
        message=message,
        source=source,
        line=err.lineno,
        column=err.colno,
        hint=hint,
    )


def _format_yaml_issue(source: str | None, err: YAMLError) -> SyntaxIssue:
    line: int | None = None
    column: int | None = None
    message = "Erreur YAML inconnue"
    hint = None

    mark = getattr(err, "problem_mark", None)
    if mark is not None:
        line = mark.line + 1
        column = mark.column + 1

    problem = getattr(err, "problem", None)
    context = getattr(err, "context", None)

    if problem and context:
        message = str(problem)
        hint = str(context)
    elif problem:
        message = str(problem)
    else:
        message = str(err).strip() or message

    return SyntaxIssue(
        parser="yaml",
        message=message,
        source=source,
        line=line,
        column=column,
        hint=hint,
    )


def load_text(text: str, *, source: str | None = None, format: Format = "auto") -> Any:
    """Charge un texte JSON ou YAML.

    Parameters
    ----------
    text:
        Contenu de la configuration.
    source:
        Nom de fichier ou identifiant du flux, uniquement utilisé pour les
        messages d'erreur.
    format:
        "json", "yaml" ou "auto" pour essayer les deux.
    """

    errors: list[SyntaxIssue] = []

    def _should_try(fmt: Format, target: Literal["json", "yaml"]) -> bool:
        return fmt == target or fmt == "auto"

    if _should_try(format, "json"):
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:  # pragma: no cover - info branch
            errors.append(_format_json_issue(source, exc))
            if format == "json":
                raise ConfigSyntaxError(errors) from exc

    if _should_try(format, "yaml"):
        try:
            return safe_load(text)
        except YAMLError as exc:
            errors.append(_format_yaml_issue(source, exc))

    if errors:
        raise ConfigSyntaxError(errors)

    raise ValueError(f"Format inconnu: {format}")


def load_file(path: str | Path, *, format: Format = "auto", encoding: str = "utf-8") -> Any:
    """Charge une configuration depuis un fichier."""

    path = Path(path)
    if format == "auto":
        suffix = path.suffix.lower()
        if suffix == ".json":
            format = "json"
        elif suffix in {".yml", ".yaml"}:
            format = "yaml"

    text = path.read_text(encoding=encoding)
    return load_text(text, source=str(path), format=format)


__all__ = ["ConfigSyntaxError", "SyntaxIssue", "load_file", "load_text"]


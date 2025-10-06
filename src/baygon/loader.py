"""Format-agnostic YAML/JSON loading with syntax error handling.

This module provides a minimal I/O layer for the "baygon" DSL. It can
load text or files and convert them to Python objects by trying the JSON
and YAML parsers in sequence. Syntax errors are collected so a CLI can
display them in a user-friendly way.
"""

from __future__ import annotations

import json
import errno
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Literal

from yaml import YAMLError, safe_load

Format = Literal["auto", "json", "yaml"]

_SEARCH_PREFIXES: tuple[str, ...] = ("baygon", "test", "tests")
_SEARCH_EXTENSIONS: tuple[str, ...] = (".yaml", ".yml", ".json")


@dataclass(slots=True)
class SyntaxIssue:
    """Describe a syntax error detected by a parser."""

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
    """Raised when the configuration has syntax errors."""

    def __init__(self, issues: Iterable[SyntaxIssue]):
        self.issues = list(issues)
        if not self.issues:
            raise ValueError("ConfigSyntaxError requires at least one error")
        super().__init__("\n".join(issue.to_message() for issue in self.issues))


def _iter_search_directories(start: Path) -> Iterator[Path]:
    current = start
    while True:
        yield current
        if (current / ".git").exists():
            break
        parent = current.parent
        if parent == current:
            break
        current = parent


def _format_not_found(message: str, *, filename: str | None = None) -> FileNotFoundError:
    return FileNotFoundError(errno.ENOENT, message, filename)


def locate_config_file(
    name: str | Path | None = None, *, start_dir: Path | None = None
) -> Path:
    """Locate a configuration file following Baygon's discovery rules.

    The search honours the following rules:

    1. Candidate files must end with ``.yaml``, ``.yml`` or ``.json``.
    2. File names starting with ``baygon`` are preferred, then ``test`` and
       finally ``tests``.
    3. Lookup starts from ``start_dir`` (or ``Path.cwd()`` when omitted) and
       walks up the directory tree until the filesystem root or the first
       directory containing a ``.git`` entry.

    Parameters
    ----------
    name:
        Optional explicit file to locate. It can be a file name or a path. When
        omitted the discovery rules above are used.
    start_dir:
        Directory where the search starts. Defaults to the current working
        directory.
    """

    start_dir = (start_dir or Path.cwd()).resolve()

    candidate: Path | None = None
    target_name: str | None = None

    if name is not None:
        candidate = Path(name)
        if candidate.is_absolute():
            if candidate.is_file():
                return candidate
            message = f"Could not find configuration file '{candidate}'."
            raise _format_not_found(message, filename=str(candidate))

        candidate_in_start = (start_dir / candidate).resolve()
        if candidate_in_start.is_file():
            return candidate_in_start

        if candidate.parts and len(candidate.parts) > 1:
            message = f"Could not find configuration file '{candidate}'."
            raise _format_not_found(message, filename=str(candidate))

        target_name = candidate.name

    search_directories = tuple(_iter_search_directories(start_dir))

    if target_name:
        for directory in search_directories:
            potential = directory / target_name
            if potential.is_file():
                return potential
            if Path(target_name).suffix:
                continue
            for extension in _SEARCH_EXTENSIONS:
                potential_with_ext = directory / f"{target_name}{extension}"
                if potential_with_ext.is_file():
                    return potential_with_ext

    for directory in search_directories:
        for prefix in _SEARCH_PREFIXES:
            for extension in _SEARCH_EXTENSIONS:
                for path in sorted(directory.glob(f"{prefix}*{extension}")):
                    if path.is_file():
                        return path

    if name is None:
        message = f"Could not locate a configuration file starting from '{start_dir}'."
    else:
        message = f"Could not find configuration file '{name}'."
    raise _format_not_found(message, filename=str(name) if name else None)


def _format_json_issue(source: str | None, err: json.JSONDecodeError) -> SyntaxIssue:
    hint = None
    message = err.msg
    if "Expecting property name" in err.msg:
        hint = "JSON keys must be enclosed in double quotes"
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
    message = "Unknown YAML error"
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
    """Load JSON or YAML text.

    Parameters
    ----------
    text:
        Configuration content.
    source:
        File name or stream identifier, only used for error messages.
    format:
        "json", "yaml" or "auto" to try both.
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

    raise ValueError(f"Unknown format: {format}")


def load_file(
    path: str | Path | None = None,
    *,
    format: Format = "auto",
    encoding: str = "utf-8",
    start_dir: Path | None = None,
) -> Any:
    """Load a configuration from a file."""

    resolved_path = locate_config_file(path, start_dir=start_dir)

    if format == "auto":
        suffix = resolved_path.suffix.lower()
        if suffix == ".json":
            format = "json"
        elif suffix in {".yml", ".yaml"}:
            format = "yaml"

    text = resolved_path.read_text(encoding=encoding)
    return load_text(text, source=str(resolved_path), format=format)


__all__ = ["ConfigSyntaxError", "SyntaxIssue", "load_file", "load_text", "locate_config_file"]

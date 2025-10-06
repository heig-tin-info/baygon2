"""Tests for the Baygon CLI."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from baygon.cli import app

runner = CliRunner()


def write_file(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_check_valid_file(tmp_path: Path) -> None:
    config = write_file(tmp_path / "good.yml", "name: Baygon\n")

    result = runner.invoke(app, ["check", str(config)])

    assert result.exit_code == 0
    assert "Configuration looks good" in result.stdout


def test_check_invalid_file(tmp_path: Path) -> None:
    config = write_file(tmp_path / "bad.yml", "items: [1, 2\n")

    result = runner.invoke(app, ["check", str(config)])

    assert result.exit_code == 1
    assert "Syntax error" in result.stderr
    assert "[yaml]" in result.stderr


def test_check_missing_file(tmp_path: Path) -> None:
    config = tmp_path / "missing.yml"

    result = runner.invoke(app, ["check", str(config)])

    assert result.exit_code == 1
    assert "Could not read" in result.stderr

from __future__ import annotations

from pathlib import Path

import pytest

from baygon.loader import (
    ConfigSyntaxError,
    SyntaxIssue,
    load_file,
    load_text,
    locate_config_file,
)


def test_load_text_json():
    data = load_text('{"name": 1}', format="json", source="inline.json")
    assert data == {"name": 1}


def test_load_text_yaml():
    yaml_text = """
    steps:
      - run: echo "hello"
    """
    data = load_text(yaml_text, format="yaml", source="inline.yaml")
    assert data == {"steps": [{"run": 'echo "hello"'}]}


def test_load_file_detects_format(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"answer": 42}', encoding="utf-8")
    assert load_file(path) == {"answer": 42}


def test_locate_config_file_prefers_prefix_and_extension(tmp_path: Path) -> None:
    (tmp_path / "baygon.json").write_text("{}", encoding="utf-8")
    preferred = tmp_path / "baygon.yaml"
    preferred.write_text("name: preferred\n", encoding="utf-8")

    located = locate_config_file(start_dir=tmp_path)

    assert located == preferred


def test_locate_config_file_stops_at_git_root(tmp_path: Path) -> None:
    project = tmp_path / "project"
    nested = project / "nested"
    nested.mkdir(parents=True)
    (project / ".git").mkdir()
    target = project / "test.yaml"
    target.write_text("value: 1\n", encoding="utf-8")

    located = locate_config_file(start_dir=nested)

    assert located == target


def test_locate_config_file_raises_when_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        locate_config_file("unknown.yaml", start_dir=tmp_path)


def test_load_file_discovers_config(tmp_path: Path) -> None:
    config_dir = tmp_path / "app" / "configs"
    config_dir.mkdir(parents=True)
    config = config_dir / "baygon.yml"
    config.write_text("answer: 42\n", encoding="utf-8")

    nested_dir = config_dir / "nested"
    nested_dir.mkdir()

    data = load_file(start_dir=nested_dir)

    assert data == {"answer": 42}


def test_json_error_contains_location():
    with pytest.raises(ConfigSyntaxError) as excinfo:
        load_text("{foo: 1}", format="json", source="broken.json")

    (issue,) = excinfo.value.issues
    assert issue.parser == "json"
    assert issue.source == "broken.json"
    assert issue.line == 1
    assert issue.column is not None
    assert "double quotes" in (issue.hint or "")


def test_auto_collects_all_errors():
    bad_text = "steps: [\n  - run: echo\n"
    with pytest.raises(ConfigSyntaxError) as excinfo:
        load_text(bad_text, source="broken.yml")

    parsers = {issue.parser for issue in excinfo.value.issues}
    assert parsers == {"json", "yaml"}
    assert all(issue.source == "broken.yml" for issue in excinfo.value.issues)


def test_invalid_format_raises_value_error():
    with pytest.raises(ValueError):
        load_text("{}", format="toml")  # type: ignore[arg-type]


def test_syntax_issue_formatting_variants():
    issue = SyntaxIssue(parser="yaml", message="Error")
    assert issue.format_location() == "<string>"
    assert issue.to_message() == "[yaml] <string>: Error"

    issue_with_line = SyntaxIssue(parser="json", message="Oops", source="cfg", line=2)
    assert issue_with_line.format_location() == "cfg:2"

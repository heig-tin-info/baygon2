from __future__ import annotations

import pytest

from baygon.loader import ConfigSyntaxError, SyntaxIssue, load_file, load_text


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


def test_json_error_contains_location():
    with pytest.raises(ConfigSyntaxError) as excinfo:
        load_text("{foo: 1}", format="json", source="broken.json")

    (issue,) = excinfo.value.issues
    assert issue.parser == "json"
    assert issue.source == "broken.json"
    assert issue.line == 1
    assert issue.column is not None
    assert "guillemets" in (issue.hint or "")


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
    issue = SyntaxIssue(parser="yaml", message="Erreur")
    assert issue.format_location() == "<string>"
    assert issue.to_message() == "[yaml] <string>: Erreur"

    issue_with_line = SyntaxIssue(parser="json", message="Oops", source="cfg", line=2)
    assert issue_with_line.format_location() == "cfg:2"

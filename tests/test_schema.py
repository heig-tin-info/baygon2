import pytest
from pydantic import ValidationError

from baygon.schema import (
    normalize_spec,
    Spec,
    ExecConfig,
    TestCase,
    Filter,
    Check,
    StreamOp,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MINIMAL = {
    "version": 1,
    "exec": {"cmd": "./a.out"},
    "tests": [
        {"name": "suite", "tests": [{"name": "t1"}]},
    ],
}


# ---------------------------------------------------------------------------
# Core happy-paths
# ---------------------------------------------------------------------------

def test_minimal_spec_valid():
    spec = normalize_spec(MINIMAL)
    assert isinstance(spec, Spec)
    assert spec.version == 1
    assert spec.exec.cmd == "./a.out"
    assert len(spec.tests) == 1
    assert spec.tests[0].name == "suite"
    assert spec.tests[0].tests and spec.tests[0].tests[0].name == "t1"


def test_args_and_stdin_coercions():
    data = {
        **MINIMAL,
        "exec": {"cmd": "prog", "args": [1, True, 3.14], "stdin": ["a", 2, False]},
        "tests": [{"name": "t"}],
    }
    spec = normalize_spec(data)
    assert spec.exec.args == ["1", "True", "3.14"]
    assert spec.exec.stdin == ["a", "2", "False"]


def test_filters_compact_and_canonical_on_root():
    data = {
        **MINIMAL,
        "filters": [
            {"trim": {}},
            {"sub": "s/\\s+//g"},
            {"sub": {"regex": "foo", "repl": "bar", "flags": "mi"}},
            {"lower": {}},
            {"upper": {}},
            {"map_eval": {"expr": "value.strip()"}},
        ],
        "tests": [{"name": "t"}],
    }
    spec = normalize_spec(data)
    kinds = [op.kind for op in spec.filters]
    assert kinds == ["trim", "sub", "sub", "lower", "upper", "map_eval"]
    # vérifie la normalisation du sub perl-like
    fsub = spec.filters[1]
    assert fsub.regex == "\\s+" and fsub.repl == "" and "g" in (fsub.flags or "")


def test_checks_compact_vs_canonical_and_numbers():
    data = {
        **MINIMAL,
        "tests": [
            {
                "name": "t",
                "stdout": [
                    {"contains": "Version"},
                    {"contains": {"value": "Build", "explain": "doit mentionner Build"}},
                    {"equals": 42},
                    {"lt": 3.5},
                    {"gte": {"value": 1, "explaination": ">=1"}},
                    {"check_eval": "int(value) % 2 == 0"},
                ],
            }
        ],
    }
    spec = normalize_spec(data)
    sops = spec.tests[0].stdout
    kinds = [op.kind for op in sops]
    assert kinds == ["contains", "contains", "equals", "lt", "gte", "check_eval"]
    # coercions
    assert sops[2].value == "42"  # equals → string coercion
    assert sops[3].value == 3.5    # lt → float coercion
    assert sops[4].explain == ">=1"  # explaination alias


def test_match_and_sub_perl_like_syntax():
    data = {
        **MINIMAL,
        "tests": [
            {
                "name": "t",
                "stdout": [
                    {"match": "m/\\b\\d+\\.\\d+\\.\\d+\\b/im"},
                    {"sub": "s/\\s+//g"},
                ],
            }
        ],
    }
    spec = normalize_spec(data)
    sops = spec.tests[0].stdout
    assert sops[0].kind == "match" and sops[0].flags == "im"
    assert sops[0].regex == "\\b\\d+\\.\\d+\\.\\d+\\b"
    assert sops[1].kind == "sub" and sops[1].flags and "g" in sops[1].flags


def test_stream_ops_mixed_order_preserved():
    data = {
        **MINIMAL,
        "tests": [
            {
                "name": "t",
                "stdout": [
                    {"trim": {}},
                    {"contains": "A"},
                    {"sub": {"regex": "x", "repl": "y", "flags": "g"}},
                    {"equals": "B"},
                ],
            }
        ],
    }
    spec = normalize_spec(data)
    sops = spec.tests[0].stdout
    assert [op.kind for op in sops] == ["trim", "contains", "sub", "equals"]


def test_capture_nested_checks():
    data = {
        **MINIMAL,
        "tests": [
            {
                "name": "t",
                "stdout": [
                    {
                        "capture": {
                            "regex": "(\\d+)",
                            "tests": [
                                {"equals": "3"},
                                {"lt": 5},
                                {"match": "m/\\d+/"},
                            ],
                        }
                    }
                ],
            }
        ],
    }
    spec = normalize_spec(data)
    cap = spec.tests[0].stdout[0]
    assert cap.kind == "capture"
    assert cap.group == 1 and cap.regex == "(\\d+)"
    assert [c.kind for c in cap.tests] == ["equals", "lt", "match"]


def test_files_section_accepts_list_or_ops_key():
    data = {
        **MINIMAL,
        "tests": [
            {
                "name": "t",
                "files": {
                    "foo.txt": [
                        {"trim": {}},
                        {"contains": "bar"},
                    ],
                    "bar.txt": {
                        "ops": [
                            {"sub": "s/a/b/g"},
                            {"equals": "ok"},
                        ]
                    },
                    "baz.txt": {
                        "filters": [{"lower": {}}],
                        "checks": [{"not_contains": "ERR"}],
                    },
                },
            }
        ],
    }
    spec = normalize_spec(data)
    f = spec.tests[0].files
    assert set(f.keys()) == {"foo.txt", "bar.txt", "baz.txt"}
    assert [op.kind for op in f["foo.txt"].ops] == ["trim", "contains"]
    assert [op.kind for op in f["bar.txt"].ops] == ["sub", "equals"]
    assert [op.kind for op in f["baz.txt"].ops] == ["lower", "not_contains"]


def test_setup_teardown_and_repeat_and_exit():
    data = {
        **MINIMAL,
        "tests": [
            {
                "name": "t",
                "repeat": 3,
                "exit": 0,
                "setup": [{"run": "echo pre"}, {"eval": "x=1"}],
                "teardown": [{"run": "echo post"}],
            }
        ],
    }
    spec = normalize_spec(data)
    t = spec.tests[0]
    assert t.repeat == 3 and t.exit == 0
    assert [s.kind for s in t.setup] == ["run", "eval"]
    assert [s.kind for s in t.teardown] == ["run"]


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------

def test_unknown_filter_error():
    data = {
        **MINIMAL,
        "filters": [{"unknown": {}}],
        "tests": [{"name": "t"}],
    }
    with pytest.raises(ValidationError) as ei:
        normalize_spec(data)
    assert "Filtre inconnu" in str(ei.value)


def test_unknown_check_error():
    data = {
        **MINIMAL,
        "tests": [
            {"name": "t", "stdout": [{"bogus": 1}]},
        ],
    }
    with pytest.raises(ValidationError) as ei:
        normalize_spec(data)
    assert "Check inconnu" in str(ei.value)


def test_stream_item_must_be_single_key_object():
    data = {
        **MINIMAL,
        "tests": [
            {"name": "t", "stdout": [
                {"contains": "A", "equals": "B"},  # deux clés -> erreur
            ]},
        ],
    }
    with pytest.raises(ValidationError) as ei:
        normalize_spec(data)
    assert "une seule clé" in str(ei.value)


def test_files_wrong_shape():
    data = {
        **MINIMAL,
        "tests": [
            {"name": "t", "files": {"foo": 123}},
        ],
    }
    with pytest.raises(ValidationError):
        normalize_spec(data)


def test_match_accepts_plain_regex_string():
    data = {
        **MINIMAL,
        "tests": [
            {"name": "t", "stdout": [{"match": "^ok$"}]},
        ],
    }
    spec = normalize_spec(data)
    op = spec.tests[0].stdout[0]
    assert op.kind == "match" and op.regex == "^ok$" and op.flags is None


def test_contains_explain_aliases():
    data = {
        **MINIMAL,
        "tests": [
            {
                "name": "t",
                "stdout": [
                    {"contains": {"value": "x", "explanation": "E1"}},
                    {"contains": {"value": "y", "explaination": "E2"}},
                ],
            }
        ],
    }
    spec = normalize_spec(data)
    sops = spec.tests[0].stdout
    assert sops[0].explain == "E1"
    assert sops[1].explain == "E2"

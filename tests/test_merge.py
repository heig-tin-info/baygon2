from __future__ import annotations

from baygon.merge import merge_spec
from baygon.schema import normalize_spec


def test_merge_propagates_filters_timeout_ulimit():
    raw_spec = {
        "version": 2,
        "exec": {
            "cmd": "prog",
            "args": ["--root"],
            "stdin": ["root"],
        },
        "filters": [{"lower": {}}],
        "timeout": 2,
        "ulimit": {"cpu": 1},
        "tests": [
            {
                "name": "Test",
                "args": ["--child"],
                "filters": [{"upper": {}}],
                "ulimit": {"mem": 2048},
            }
        ],
    }

    spec = normalize_spec(raw_spec)
    merged = merge_spec(spec)

    (test,) = merged.tests
    assert [f.kind for f in test.filters] == ["lower", "upper"]
    assert test.args == ["--root", "--child"]
    assert test.timeout == 2
    assert test.ulimit == {"cpu": 1, "mem": 2048}
    assert test.stdin == ["root"]


def test_nested_tests_merge_inheritance_and_override():
    raw_spec = {
        "version": 2,
        "exec": {
            "cmd": "prog",
            "args": ["--root"],
        },
        "filters": [{"lower": {}}],
        "timeout": 2,
        "ulimit": {"cpu": 10},
        "tests": [
            {
                "name": "Parent",
                "args": ["--parent"],
                "filters": [{"upper": {}}],
                "timeout": 5,
                "ulimit": {"cpu": 5},
                "tests": [
                    {
                        "name": "Child",
                        "args": ["--child"],
                        "filters": [{"trim": {}}],
                        "ulimit": {"mem": 1024},
                    }
                ],
            }
        ],
    }

    spec = normalize_spec(raw_spec)
    merged = merge_spec(spec)

    (parent,) = merged.tests
    assert parent.tests is not None
    (child,) = parent.tests

    assert [f.kind for f in parent.filters] == ["lower", "upper"]
    assert parent.timeout == 5
    assert parent.ulimit == {"cpu": 5}

    assert [f.kind for f in child.filters] == ["lower", "upper", "trim"]
    assert child.timeout == 5
    assert child.ulimit == {"cpu": 5, "mem": 1024}
    assert child.args == ["--root", "--parent", "--child"]

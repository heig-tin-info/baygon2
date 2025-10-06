import math

import pytest

from baygon.matchers import (
    Matchers,
    build_matcher,
    iter_matchers,
    matcher_registry,
)


def test_registry_contains_builtins():
    names = {name for name, _ in iter_matchers()}
    assert {
        "match",
        "contains",
        "not_contains",
        "equals",
        "not_equals",
        "lt",
        "lte",
        "gt",
        "gte",
        "check_eval",
        "capture",
    }.issubset(names)


def test_regex_matcher_success_and_failure():
    matcher = matcher_registry.create("match", regex=r"foo")
    assert matcher("foobar") is None
    failure = matcher("bar")
    assert failure is not None
    assert "does not match" in str(failure)


def test_contains_and_not_contains():
    contains = matcher_registry.create("contains", value="needle")
    assert contains("haystack needle haystack") is None
    failure = contains("haystack")
    assert failure is not None
    assert "does not contain" in str(failure)

    not_contains = matcher_registry.create("not_contains", value="needle")
    assert not_contains("haystack") is None
    failure = not_contains("haystack needle")
    assert failure is not None
    assert "unexpectedly contains" in str(failure)


def test_equals_and_not_equals():
    equals = matcher_registry.create("equals", value="foo")
    assert equals("foo") is None
    failure = equals("bar")
    assert failure is not None
    assert "does not equal" in str(failure)

    not_equals = matcher_registry.create("not_equals", value="foo")
    assert not_equals("bar") is None
    failure = not_equals("foo")
    assert failure is not None
    assert "unexpectedly equals" in str(failure)


@pytest.mark.parametrize(
    "kind, expected, samples",
    [
        ("lt", 10, [(5, True), (10, False)]),
        ("lte", 10, [(10, True), (11, False)]),
        ("gt", 10, [(11, True), (10, False)]),
        ("gte", 10, [(10, True), (9, False)]),
    ],
)
    
def test_numeric_matchers(kind, expected, samples):
    matcher = matcher_registry.create(kind, value=expected)
    for sample, ok in samples:
        result = matcher(sample)
        if ok:
            assert result is None
        else:
            assert result is not None


def test_match_eval_with_namespace():
    matcher = matcher_registry.create("check_eval", expr="math.isclose(value, target)")
    failure = matcher(1.0, namespace={"math": math, "target": 2.0})
    assert failure is not None
    success = matcher(2.0, namespace={"math": math, "target": 2.0})
    assert success is None


def test_capture_nested_checks():
    matcher = build_matcher(
        {
            "capture": {
                "regex": r"Hello (\\w+)",
                "group": 1,
                "tests": [
                    {"equals": "World"},
                    {"not_equals": "Error"},
                ],
            }
        }
    )
    assert matcher("Hello World") is None
    failure = matcher("Hello there")
    assert failure is not None
    assert "failed" in str(failure).lower()


def test_build_matcher_from_schema_object():
    check = {"equals": {"value": "spam", "explain": "must be spam"}}
    matcher = build_matcher(check)
    failure = matcher("eggs", on="stdout")
    assert failure is not None
    assert "stdout" in str(failure)


def test_matchers_collection_accumulates_failures():
    collection = Matchers(
        [
            matcher_registry.create("contains", value="foo"),
            matcher_registry.create("contains", value="bar"),
        ]
    )
    failures = collection.evaluate("foo baz", on="stdout")
    assert len(failures) == 1
    assert "bar" in failures[0].details

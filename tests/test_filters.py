from __future__ import annotations

import pytest

from baygon import add_filter
from baygon.filters import (
    Filter,
    FilterError,
    FilterReplace,
    Filters,
    FilterTrim,
    FilterUppercase,
    registry,
)


def test_registry_contains_builtin_filters():
    names = set(registry.keys())
    assert {"none", "uppercase", "lowercase", "trim", "ignore_spaces", "replace", "regex", "eval"} <= names


def test_schema_model_reflects_signature():
    model = FilterReplace.schema_model()
    instance = model(pattern="foo", replacement="bar")
    assert instance.pattern == "foo"
    assert instance.replacement == "bar"
    assert instance.input is False


def test_registry_create_and_apply():
    regex = registry.create("regex", pattern=r"\s+", replacement="-")
    assert regex("foo bar\tbaz") == "foo-bar-baz"


def test_filters_collection_apply_order():
    filters = Filters([FilterTrim(), FilterUppercase()])
    assert filters.apply("  hello  ") == "HELLO"


def test_add_filter_registers_custom_class():
    class FilterSuffix(Filter):
        def __init__(self, suffix: str, repeat: int = 1, *, input: bool = False) -> None:
            super().__init__(input=input)
            self.suffix = suffix
            self.repeat = repeat

        def apply(self, value: str) -> str:
            return value + self.suffix * self.repeat

    add_filter("test_suffix", FilterSuffix)
    try:
        model = registry.model("test_suffix")
        instance = model(suffix="!", repeat=2)
        assert instance.suffix == "!"
        assert instance.repeat == 2
        created = registry.create("test_suffix", suffix="?", repeat=3)
        assert created("ok") == "ok???"
    finally:
        del registry["test_suffix"]
        with pytest.raises(FilterError):
            registry.create("test_suffix")

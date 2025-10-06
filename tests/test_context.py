from __future__ import annotations

import pytest

from baygon.context import Context, ContextError


def test_execute_and_evaluate_namespace() -> None:
    ctx = Context()
    ctx.execute(
        """
foo = 21

def mul(x, y):
    return x * y
"""
    )

    assert ctx.evaluate("foo") == 21
    assert ctx.evaluate("mul(foo, 2)") == 42


def test_render_with_mustaches_and_format() -> None:
    ctx = Context(initial={"i": 4, "name": "Alice"})
    rendered = ctx.render("{{ name }} a {{ i++/2:.1f }} kg de pommes")
    assert rendered == "Alice a 2.0 kg de pommes"
    assert ctx["i"] == 5


def test_render_handles_pre_and_post_increment() -> None:
    ctx = Context()
    ctx.execute("i = 1")
    rendered = ctx.render("{{ i++ }} {{ i }} {{ ++i }}")
    assert rendered == "1 2 3"
    assert ctx["i"] == 3


def test_render_value_recurses() -> None:
    ctx = Context()
    ctx.execute("x = 1\ny = 2")
    payload = {
        "single": "{{ x }}",
        "list": ["{{ y }}", "static"],
        "tuple": ("{{ x + y }}",),
    }
    result = ctx.render_value(payload)
    assert result == {
        "single": "1",
        "list": ["2", "static"],
        "tuple": ("3",),
    }


def test_render_raises_context_error_with_expression() -> None:
    ctx = Context()
    with pytest.raises(ContextError) as excinfo:
        ctx.render("{{ missing }}")
    err = excinfo.value
    assert err.expression == "missing"
    assert err.template == "{{ missing }}"


def test_invalid_expression_reports_error() -> None:
    ctx = Context()
    with pytest.raises(ContextError):
        ctx.evaluate("1 +")


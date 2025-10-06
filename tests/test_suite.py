from baygon.merge import merge_spec
from baygon.schema import normalize_spec
from baygon.suite import TestRunResult, build_suite


def _build_suite(raw_spec: dict) -> tuple:
    spec = normalize_spec(raw_spec)
    merged = merge_spec(spec)
    suite = build_suite(merged)
    return suite, merged


def test_build_suite_injects_dependencies():
    raw = {
        "version": 1,
        "exec": {
            "cmd": [
                "python",
                "-c",
                "import sys; data = sys.stdin.read(); print(data, end='')",
            ]
        },
        "filters": [{"trim": {}}],
        "tests": [
            {
                "name": "group",
                "tests": [
                    {
                        "name": "echo",
                        "stdin": "hello",
                        "filters": [{"lower": {}}],
                        "stdout": [
                            {"map_eval": "value.upper()"},
                            {"equals": "HELLO"},
                        ],
                    }
                ],
            }
        ],
    }

    suite, _ = _build_suite(raw)
    assert len(suite.tests) == 1
    group = suite.tests[0]
    assert group.runtime is None
    assert len(group.tests) == 1
    leaf = group.tests[0]
    assert leaf.runtime is not None
    runtime = leaf.runtime
    assert runtime.filters  # root + local filters injected
    assert runtime.streams["stdout"] is not None
    stdout_steps = runtime.streams["stdout"]._steps
    assert stdout_steps and stdout_steps[0].filter.__class__.__name__.startswith("Filter")


def test_run_leaf_collects_outputs_and_filters(tmp_path):
    script = tmp_path / "script.py"
    script.write_text(
        "import sys\n"
        "data = sys.stdin.read()\n"
        "print(data, end='')\n"
    )

    raw = {
        "version": 1,
        "exec": {
            "cmd": [
                "python",
                str(script),
            ]
        },
        "filters": [{"trim": {}}],
        "tests": [
            {
                "name": "group",
                "tests": [
                    {
                        "name": "echo",
                        "stdin": "hello",
                        "filters": [{"lower": {}}],
                        "stdout": [
                            {"map_eval": "value.upper()"},
                            {"equals": "HELLO"},
                        ],
                    }
                ],
            }
        ],
    }

    suite, _ = _build_suite(raw)
    result = suite.tests[0].tests[0].run()
    assert isinstance(result, TestRunResult)
    assert result.passed
    assert len(result.iterations) == 1
    iteration = result.iterations[0]
    assert iteration.stdin == "hello"
    stdout = iteration.streams["stdout"]
    assert stdout.original.strip() == "hello"
    assert stdout.filtered == "HELLO"
    history = [step.name for step in stdout.filters]
    assert history == ["trim", "lowercase", "map_eval"]


def test_suite_run_executes_all(tmp_path):
    script = tmp_path / "script.py"
    script.write_text("print('ok')\n")

    raw = {
        "version": 1,
        "exec": {"cmd": ["python", str(script)]},
        "tests": [{"name": "single", "stdout": [{"contains": "ok"}]}],
    }

    suite, _ = _build_suite(raw)
    results = suite.run()
    assert len(results) == 1
    assert results[0].passed

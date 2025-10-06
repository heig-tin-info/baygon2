"""Build and execute runtime test suites from normalized specifications."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

from .context import Context
from .executable import Executable
from .filters import Filter, registry as filter_registry
from .matchers import Matcher, MatcherError, build_matcher
from .schema import FilterBase, FMapEval, FSub, Spec, StreamOp, TestCase
from .ids import TestId

__all__ = [
    "FilterApplication",
    "StreamEvaluation",
    "IterationResult",
    "TestRunResult",
    "TestNode",
    "TestSuite",
    "build_suite",
]


@dataclass(slots=True)
class FilterApplication:
    """Describe how a filter transformed a value."""

    name: str
    before: str
    after: str


@dataclass(slots=True)
class StreamEvaluation:
    """Outcome of applying filters and checks on a stream."""

    name: str
    original: str
    filtered: str
    filters: list[FilterApplication] = field(default_factory=list)
    failures: list[MatcherError] = field(default_factory=list)


@dataclass(slots=True)
class IterationResult:
    """Result of a single execution of a test."""

    index: int
    command: list[str]
    args: list[str]
    stdin: str | None
    exit_status: int
    expected_exit: int | None
    streams: dict[str, StreamEvaluation]
    files: dict[str, StreamEvaluation]
    failures: list[MatcherError] = field(default_factory=list)


@dataclass(slots=True)
class TestRunResult:
    """Aggregate result for a test (possibly repeated multiple times)."""

    __test__ = False
    test_id: TestId
    name: str
    description: str | None
    iterations: list[IterationResult]
    failures: list[MatcherError]

    @property
    def passed(self) -> bool:
        return not self.failures


@dataclass(slots=True)
class _FilterStep:
    filter: Filter


@dataclass(slots=True)
class _MatcherStep:
    matcher: Matcher


PipelineStep = _FilterStep | _MatcherStep


def _instantiate_filter(filter_config: FilterBase) -> Filter:
    """Return a runtime :class:`~baygon.filters.Filter` from schema configuration."""

    kind = filter_config.kind
    if kind == "trim":
        return filter_registry.create("trim")
    if kind == "lower":
        return filter_registry.create("lowercase")
    if kind == "upper":
        return filter_registry.create("uppercase")
    if kind == "sub":
        assert isinstance(filter_config, FSub)
        return filter_registry.create(
            "regex",
            pattern=filter_config.regex,
            replacement=filter_config.repl,
            flags=filter_config.flags,
        )
    if kind == "map_eval":
        assert isinstance(filter_config, FMapEval)
        return filter_registry.create("map_eval", expr=filter_config.expr)
    raise ValueError(f"Unsupported filter kind: {kind}")


def _build_pipeline(ops: Iterable[StreamOp]) -> list[PipelineStep]:
    pipeline: list[PipelineStep] = []
    for op in ops:
        if isinstance(op, FilterBase):
            pipeline.append(_FilterStep(_instantiate_filter(op)))
        else:
            matcher = build_matcher(op)
            pipeline.append(_MatcherStep(matcher))
    return pipeline


def _render_stdin(ctx: Context, template: str | Sequence[str] | None) -> str | None:
    if template is None:
        return None
    rendered = ctx.render_value(template)
    if rendered is None:
        return None
    if isinstance(rendered, list | tuple):
        return "".join(str(item) for item in rendered)
    return str(rendered)


def _render_args(ctx: Context, args: Sequence[str]) -> list[str]:
    rendered = ctx.render_value(list(args))
    return [str(arg) for arg in rendered]


def _apply_filter(filter_: Filter, value: str, history: list[FilterApplication]) -> str:
    before = value
    after = filter_.filter(value)
    history.append(FilterApplication(filter_.__class__.name(), before, after))
    return after


class _StreamRuntime:
    """Execute stream filters and matchers."""

    def __init__(self, steps: list[PipelineStep]) -> None:
        self._steps = steps

    def evaluate(
        self,
        value: str,
        *,
        stream_name: str,
        test_id: TestId,
        global_filters: Sequence[Filter],
        ctx: Context,
    ) -> StreamEvaluation:
        history: list[FilterApplication] = []
        failures: list[MatcherError] = []
        current = value

        for filter_ in global_filters:
            current = _apply_filter(filter_, current, history)

        for step in self._steps:
            if isinstance(step, _FilterStep):
                current = _apply_filter(step.filter, current, history)
            else:
                context = {
                    "on": stream_name,
                    "test": str(test_id),
                    "namespace": ctx.namespace,
                }
                failure = step.matcher(current, **context)
                if failure is not None:
                    failures.append(failure)

        return StreamEvaluation(
            name=stream_name,
            original=value,
            filtered=current,
            filters=history,
            failures=failures,
        )


class _TestRuntime:
    """Runtime representation of an executable test case."""

    def __init__(
        self,
        *,
        test_id: TestId,
        case: TestCase,
        executable: Executable,
        base_cmd_args: list[str],
    ) -> None:
        self.test_id = test_id
        self.case = case
        self.executable = executable
        self.base_cmd_args = base_cmd_args
        self.filters: list[Filter] = [_instantiate_filter(f) for f in case.filters]
        self.streams = {
            "stdout": _StreamRuntime(_build_pipeline(case.stdout)),
            "stderr": _StreamRuntime(_build_pipeline(case.stderr)),
        }
        self.files = {
            name: _StreamRuntime(_build_pipeline(spec.ops))
            for name, spec in case.files.items()
        }

    def _limits(self) -> tuple[int | None, int | None, int | None]:
        limits = self.case.ulimit or {}
        cpu = limits.get("cpu")
        mem = limits.get("mem") or limits.get("memory")
        nproc = limits.get("nproc")
        return cpu, mem, nproc

    def _run_hooks(self, ctx: Context, hooks: Sequence[Any]) -> None:
        for step in hooks:
            rendered = ctx.render(step.value)
            if step.kind == "eval":
                ctx.execute(rendered)
            else:
                subprocess.run(rendered, shell=True, check=True)

    def run(self) -> TestRunResult:
        ctx = Context()
        iterations: list[IterationResult] = []
        failures: list[MatcherError] = []

        try:
            self._run_hooks(ctx, self.case.setup)
        except Exception as exc:  # pragma: no cover - defensive
            failures.append(
                MatcherError(
                    value=None,
                    expected=None,
                    on="setup",
                    check="setup",
                    details=f"Setup failed: {exc}",
                )
            )
            return TestRunResult(self.test_id, self.case.name, self.case.description, iterations, failures)

        cpu, mem, nproc = self._limits()
        repeat = max(self.case.repeat, 1)

        for index in range(1, repeat + 1):
            rendered_args = _render_args(ctx, self.case.args)
            stdin = _render_stdin(ctx, self.case.stdin)
            command = [self.executable.filename, *self.base_cmd_args, *rendered_args]

            outputs = self.executable.run(
                *self.base_cmd_args,
                *rendered_args,
                stdin=stdin,
                timeout=self.case.timeout,
                cpu_time=cpu,
                mem_bytes=mem,
                nproc=nproc,
            )

            stream_results: dict[str, StreamEvaluation] = {}
            stream_failures: list[MatcherError] = []
            for name in ("stdout", "stderr"):
                runtime = self.streams[name]
                text = getattr(outputs, name)
                evaluation = runtime.evaluate(
                    text,
                    stream_name=name,
                    test_id=self.test_id,
                    global_filters=self.filters,
                    ctx=ctx,
                )
                stream_results[name] = evaluation
                stream_failures.extend(evaluation.failures)

            file_results: dict[str, StreamEvaluation] = {}
            file_failures: list[MatcherError] = []
            for fname, runtime in self.files.items():
                try:
                    content = Path(fname).read_text()
                except FileNotFoundError:
                    failure = MatcherError(
                        value=None,
                        expected=fname,
                        on=fname,
                        check="exists",
                        details=f"File '{fname}' not found",
                    )
                    evaluation = StreamEvaluation(fname, "", "", [], [failure])
                else:
                    evaluation = runtime.evaluate(
                        content,
                        stream_name=fname,
                        test_id=self.test_id,
                        global_filters=self.filters,
                        ctx=ctx,
                    )
                file_results[fname] = evaluation
                file_failures.extend(evaluation.failures)

            exit_failures: list[MatcherError] = []
            if self.case.exit is not None and outputs.exit_status != self.case.exit:
                exit_failures.append(
                    MatcherError(
                        value=outputs.exit_status,
                        expected=self.case.exit,
                        on="exit",
                        check="exit",
                        details=(
                            f"Expected exit status {self.case.exit} but received {outputs.exit_status}"
                        ),
                    )
                )

            iteration_failures = [*stream_failures, *file_failures, *exit_failures]
            iterations.append(
                IterationResult(
                    index=index,
                    command=command,
                    args=[*self.base_cmd_args, *rendered_args],
                    stdin=stdin,
                    exit_status=outputs.exit_status,
                    expected_exit=self.case.exit,
                    streams=stream_results,
                    files=file_results,
                    failures=iteration_failures,
                )
            )
            failures.extend(iteration_failures)

        try:
            self._run_hooks(ctx, self.case.teardown)
        except Exception as exc:  # pragma: no cover - defensive
            failures.append(
                MatcherError(
                    value=None,
                    expected=None,
                    on="teardown",
                    check="teardown",
                    details=f"Teardown failed: {exc}",
                )
            )

        return TestRunResult(self.test_id, self.case.name, self.case.description, iterations, failures)


class TestNode:
    """Node of a runtime test tree."""

    __test__ = False

    def __init__(
        self,
        *,
        test_id: TestId,
        name: str,
        description: str | None,
        runtime: _TestRuntime | None,
        children: list[TestNode],
    ) -> None:
        self.test_id = test_id
        self.name = name
        self.description = description
        self.runtime = runtime
        self.tests = children

    def run(self) -> TestRunResult | list[TestRunResult]:
        if self.runtime is not None:
            return self.runtime.run()
        results: list[TestRunResult] = []
        for child in self.tests:
            outcome = child.run()
            if isinstance(outcome, list):
                results.extend(outcome)
            else:
                results.append(outcome)
        return results

    def run_all(self) -> list[TestRunResult]:
        results: list[TestRunResult] = []
        if self.runtime is not None:
            results.append(self.runtime.run())
        for child in self.tests:
            child_results = child.run_all()
            results.extend(child_results)
        return results


class TestSuite:
    """Runtime suite built from a :class:`~baygon.schema.Spec`."""

    __test__ = False

    def __init__(self, *, spec: Spec, executable: Executable, base_cmd_args: list[str]) -> None:
        self.spec = spec
        self.executable = executable
        self.base_cmd_args = base_cmd_args
        self.tests: list[TestNode] = []

    def run(self) -> list[TestRunResult]:
        results: list[TestRunResult] = []
        for node in self.tests:
            outcome = node.run()
            if isinstance(outcome, list):
                results.extend(outcome)
            else:
                results.append(outcome)
        return results


def _split_command(cmd: str | Sequence[str]) -> tuple[str, list[str]]:
    if isinstance(cmd, str):
        return cmd, []
    if not cmd:
        raise ValueError("exec.cmd must not be empty")
    head, *tail = list(cmd)
    return head, [str(chunk) for chunk in tail]


def _build_nodes(
    tests: Sequence[TestCase],
    *,
    parent_id: tuple[int, ...] = (),
    executable: Executable,
    base_cmd_args: list[str],
) -> list[TestNode]:
    nodes: list[TestNode] = []
    for index, case in enumerate(tests, start=1):
        test_id = TestId((*parent_id, index))
        children = _build_nodes(
            case.tests or [],
            parent_id=test_id.parts,
            executable=executable,
            base_cmd_args=base_cmd_args,
        )
        runtime: _TestRuntime | None
        if case.tests:
            runtime = None
        else:
            runtime = _TestRuntime(
                test_id=test_id,
                case=case,
                executable=executable,
                base_cmd_args=base_cmd_args,
            )
        node = TestNode(
            test_id=test_id,
            name=case.name,
            description=case.description,
            runtime=runtime,
            children=children,
        )
        nodes.append(node)
    return nodes


def build_suite(spec: Spec) -> TestSuite:
    """Instantiate a :class:`TestSuite` with runtime dependencies injected."""

    cmd, base_args = _split_command(spec.exec.cmd)
    executable = Executable(cmd)
    suite = TestSuite(spec=spec, executable=executable, base_cmd_args=base_args)
    suite.tests = _build_nodes(
        spec.tests,
        executable=executable,
        base_cmd_args=base_args,
    )
    return suite


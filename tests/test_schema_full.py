import pytest
import yaml

from baygon.schema import Spec, normalize_spec

EXAMPLE_V1_A = "\n".join(
    [
        "version: 1",
        "tests:",
        "  - name: Arguments check",
        "    tests:",
        "      - name: No errors if two arguments",
        "        args: [1, 2]",
        "        exit: 0",
        "      - name: Error if less than two arguments",
        "        args: [1]",
        "        exit: 1",
        "  - name: Stdout is the sum of arguments",
        "    args: [1, 2]",
        "    stdout: []",
        "  - name: Version on stderr",
        '    args: ["--version"]',
        "    stderr:",
        "      - match: 'm/\\d+\\.\\d+\\.\\d+/'",
        '      - contains: "Version"',
        "",
    ]
)

EXAMPLE_V1_B = "\n".join(
    [
        "version: 1",
        "filters:",
        "  - sub: 's/\\s+//g'",
        "tests:",
        "  - name: Stdout is the spaces are removed",
        "    args: [4, 5]",
        "    executable: add.exe.py",
        "    stdout:",
        '      - contains: "a+b=4+5"',
        "",
    ]
)

EXAMPLE_V1_C = "\n".join(
    [
        "version: 1",
        "tests:",
        "  - name: Arguments check",
        "    tests:",
        "      - name: No errors if two arguments",
        "        args: [1]",
        "        exit: 0",
        "      - name: Error if less than two arguments",
        "        args: [1]",
        "        exit: 1",
        "  - name: Stdout is the sum of arguments",
        "    args: [1, 2]",
        "    stdout:",
        "      - trim: {}",
        '      - equals: "5"',
        "  - name: Version on stderr",
        '    args: ["--version"]',
        "    stderr:",
        "      - match: 'm/\\d+\\.\\d+\\.\\d+/'",
        '      - contains: "tarton"',
        "",
    ]
)

# V2: exercice complet de la syntaxe "moderne"
EXAMPLE_V2_FULL = "\n".join(
    [
        "version: 1",
        "exec:",
        "  cmd: ./a.out",
        "  timeout: 5",
        "  args: []",
        "  env: { }",
        "  shell: false",
        "filters:",
        "  - trim: {}",
        "  - sub: 's/\\s+//g'",
        "tests:",
        "  - name: Arguments check",
        "    tests:",
        "      - name: No errors if two arguments",
        "        args: [1, 2]",
        "        exit: 0",
        "      - name: Error if less than two arguments",
        "        args: [1]",
        "        exit: 1",
        "  - name: Stdout is the sum of arguments",
        "    args: [1, 2]",
        "    stdout:",
        "      - match: 'm/\\d+\\.\\d+\\.\\d+/im'",
        '      - contains: "Version"',
        '      - sub: { regex: " ", repl: "", flags: "g" }',
        '      - equals: "3"',
        "      - capture:",
        "          regex: '(\\d+)'",
        "          tests:",
        "            - lt: 10",
        '            - check_eval: "int(value) % 3 == 0"',
        "    stderr: []",
        "    files:",
        "      output.txt:",
        "        ops:",
        "          - trim: {}",
        '          - not_contains: "Error"',
        "  - name: Version on stderr",
        '    args: ["--version"]',
        "    stderr:",
        "      - match: 'm/\\d+\\.\\d+\\.\\d+/'",
        '      - contains: { value: "Version", explain: "Should mention Version" }',
        "  - name: With setup/teardown and stdin list",
        "    setup:",
        "      - run: echo pre",
        "      - eval: x = 1",
        "    teardown:",
        "      - run: echo post",
        '    stdin: ["line1", "line2"]',
        '    args: ["--echo-stdin"]',
        "    stdout:",
        '      - contains: "line1"',
        '      - contains: "line2"',
        "",
    ]
)


def _ensure_exec(d: dict) -> dict:
    """Helper: pour les YAML v1 qui n'ont pas `exec`, on injecte un exec minimal.
    On garde le contenu intact sinon.
    """
    if "exec" not in d:
        d = {**d, "exec": {"cmd": "./a.out"}}
    return d


@pytest.mark.parametrize("raw", [EXAMPLE_V1_A, EXAMPLE_V1_B, EXAMPLE_V1_C])
def test_yaml_v1_examples_parse(raw):
    data = yaml.safe_load(raw)
    data = _ensure_exec(data)
    spec = normalize_spec(data)
    assert isinstance(spec, Spec)
    # Quelques assertions de surface
    assert spec.version == 1
    assert spec.exec is not None
    assert spec.tests and len(spec.tests) >= 1


def test_yaml_v2_full_parses():
    data = yaml.safe_load(EXAMPLE_V2_FULL)
    spec = normalize_spec(data)  # a un bloc exec complet
    assert isinstance(spec, Spec)
    # On s'assure que quelques éléments ont bien été normalisés
    assert spec.filters and spec.filters[0].kind == "trim"
    suite = spec.tests[1]  # "Stdout is the sum of arguments"
    kinds = [op.kind for op in suite.stdout]
    assert "match" in kinds and "equals" in kinds and "capture" in kinds

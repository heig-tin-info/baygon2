# DSL reference

Baygon's test specifications are written in YAML or JSON using a declarative DSL.  A
specification is a tree: global settings apply to every child node, while each
group or test case can override or extend them.

```yaml
version: 1
exec:
  cmd: ./a.out
  timeout: 5
filters:
  - trim: {}
  - sub: "s/\s+/ /g"
tests:
  - name: Arguments check
    tests:
      - name: Two numbers succeed
        args: [1, 2]
        exit: 0
      - name: Missing argument fails
        args: [1]
        exit: 1
  - name: Sum appears on stdout
    args: [1, 2]
    stdout:
      - contains: "3"
```

## Root keys

* **`version`** – schema version, currently `1`.
* **`exec`** – mandatory execution context.  All tests inherit it unless they
  provide their own values.
* **`filters`** – optional list of output filters applied to every stream of
  every test.
* **`tests`** – list of suites or leaf test cases.

### Execution context (`exec`)

```yaml
exec:
  cmd: ./app
  timeout: 5          # seconds (float accepted)
  stdin: "42\n"       # string or list of strings
  args: [--mode, fast] # always coerced to strings
  env: { DEBUG: "1" }
  cwd: ./build
  shell: false
```

Child suites inherit the execution context and may override specific fields.

## Inheritance model

Settings flow down the tree:

* `filters`, `setup`, `teardown`, `stdin`, `args`, and `env` defined on a parent
  are merged into descendants.
* Streams (`stdout`, `stderr`, `files`) are **not** inherited – they only apply
  to the node where they are declared.

## Filters

Filters transform stream data before checks are executed.  Each filter is
represented as a single-key object.  The following filters are available:

| Filter      | Effect |
| ----------- | ------ |
| `trim`      | Strip leading/trailing whitespace on every line. |
| `lower`     | Force lowercase. |
| `upper`     | Force uppercase. |
| `sub`       | Apply a regular-expression substitution. |
| `map_eval`  | Evaluate a safe Python expression to transform the value. |

Examples:

```yaml
filters:
  - trim: {}
  - lower: {}
  - sub: "s/\s+/ /g"        # Perl-like syntax
  - sub:
      regex: "[0-9]+"
      repl: "<num>"
      flags: "i"
  - map_eval: "value.replace('error', 'warning')"
```

## Stream operations

`stdout`, `stderr`, and every entry under `files` accept a **list of
operations**.  The list can mix filters and checks.  Items are executed in order
from top to bottom.

```yaml
stdout:
  - trim: {}
  - match: "m/^result:/i"
  - contains:
      value: "success"
      explain: "The tool must announce success"
```

`files` use the same format.  Declaring a file implies that it must exist:

```yaml
files:
  report.json:
    - trim: {}
    - match: "m/\"status\": \"ok\"/"
```

## Checks

The DSL ships with a concise set of checks:

| Check          | Description |
| -------------- | ----------- |
| `match`        | Regular-expression match.  Supports `m/.../flags` syntax. |
| `contains`     | The stream must contain the string. |
| `not_contains` | The stream must not contain the string. |
| `equals`       | Exact string comparison. |
| `not_equals`   | String inequality. |
| `lt`, `lte`, `gt`, `gte` | Numerical comparisons (values coerced to floats). |
| `check_eval`   | Evaluate a Python expression returning `True`.  The stream
  value is exposed as `value`. |
| `capture`      | Capture a regex group and run more checks on it. |

### Regular expressions

`match` accepts plain PCRE-compatible patterns or the Perl-like `m/.../flags`
form.  Flags follow Python's `re` module semantics (`i`, `m`, `s`, `x`, ...).

```yaml
stderr:
  - match: "m/^Version (?P<v>\d+\.\d+)/i"
```

### Numeric comparisons

Values provided to numeric comparators are coerced to floats, allowing compact
notation:

```yaml
stdout:
  - capture:
      regex: "m/score: (?P<value>\d+(?:\.\d+)?)"  # flags optional
      tests:
        - gte: 10
        - lt: 20
```

### Capture blocks

`capture` extracts a regex group (default group `1`) and executes additional
checks on the captured value:

```yaml
stdout:
  - capture:
      regex: "m/Duration: (\d+\.\d+)s/"
      tests:
        - lt:
            value: 0.5
            explain: "Execution should remain fast"
```

### Evaluated expressions

`check_eval` is the assertion counterpart to `map_eval`.  The special variable
`value` contains the current stream value:

```yaml
stdout:
  - check_eval:
      expr: "'error' not in value.lower()"
      explain: "The program must stay quiet"
```

## Setup and teardown hooks

Each suite or test can declare hooks.  Hooks inherit and extend those of their
parents.

```yaml
setup:
  - run: "./prepare-fixtures.sh"
  - eval: "ctx['tmpdir'] = mkdtemp()"
teardown:
  - run: "rm -rf {tmpdir}"
```

A hook is either `{ run: "command" }` or `{ eval: "python" }`.

## Repeating tests

`repeat` duplicates a test in the same context.  Hooks run before the first
iteration and after the last one.

```yaml
- name: Retry download
  repeat: 5
  stdout:
    - contains: "200 OK"
```

## Filesystem assertions

When `files` are declared, Baygon reads the target files after the program
finishes.  Filters and checks work exactly like on `stdout` or `stderr`.

```yaml
files:
  "logs/app.log":
    - trim: {}
    - not_contains: "Traceback"
```

## Exit status

Use `exit` to assert the program's return code.  Integers are coerced to the
`0–255` POSIX range; hexadecimal strings are accepted.

```yaml
exit: 0
```

For more advanced logic, mix numeric comparisons:

```yaml
exit:
  - gte: 0
  - lt: 64
```

## Inlining commands and arguments

`stdin` accepts a string or a list of lines.  `args` always becomes a list of
strings, which means integers or booleans are automatically coerced:

```yaml
stdin:
  - "first line\n"
  - "second line\n"
args: [42, true, "--verbose"]
```

## Templates and future extensions

The DSL is designed to stay concise.  Complex transforms should rely on
`map_eval` (for rewriting) or `check_eval` (for assertions).  Upcoming features,
like templated iterators and richer math helpers, will build on the same
foundations described above.

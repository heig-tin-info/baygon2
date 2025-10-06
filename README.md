# Baygon

[![GitHub issues](https://img.shields.io/github/issues/heig-tin-info/baygon.svg)](https://github.com/heig-tin-info/baygon/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/heig-tin-info/baygon.svg)](https://github.com/heig-tin-info/baygon/pulls)
[![GitHub last commit](https://img.shields.io/github/last-commit/heig-tin-info/baygon.svg)](https://github.com/heig-tin-info/baygon/commits/main)
[![Documentation](https://github.com/heig-tin-info/baygon/actions/workflows/docs.yml/badge.svg)](https://github.com/heig-tin-info/baygon/actions/workflows/docs.yml)
[![Codecov](https://codecov.io/github/heig-tin-info/baygon/branch/main/graph/badge.svg?token=hFuVW5z784)](https://codecov.io/github/heig-tin-info/baygon)
[![PyPI](https://img.shields.io/pypi/v/baygon.svg)](https://pypi.org/project/baygon/)
![Python](https://img.shields.io/pypi/pyversions/baygon.svg)
[![License](https://img.shields.io/github/license/heig-tin-info/baygon.svg)](LICENSE)

**K**ills **B**ugs **D**ead!

<img src="https://raw.githubusercontent.com/heig-tin-info/baygon/main/docs/baygon.svg" alt="Baygon" width="400" />

Baygon is a minimalist functional test suite for executables. Write your test scenarios as a
concise YAML or JSON file, point the runner at the program you want to verify, and get colourful,
readable results that make grading student assignments and validating CLI tools a breeze.

## Features

- ⚙️ Describe tests in YAML or JSON using a compact DSL with powerful matchers.
- 🧪 Validate any executable: binaries, scripts, Python modules, or shell pipelines.
- 🧮 Assign scores to tests and sections to support automated grading workflows.
- 📦 Ship with an ergonomic CLI powered by [Typer](https://typer.tiangolo.com/) and rich terminal
  output provided by [Rich](https://rich.readthedocs.io/).
- 📚 Extensive documentation with cookbook-style guides and scripting tips.

## Installation

Baygon is available on PyPI and supports Python 3.10 and later.

```bash
pip install baygon
```

If you use [uv](https://docs.astral.sh/uv/), you can install Baygon in an isolated environment:

```bash
uv tool install baygon
```

## Quick start

Assume you want to test the following simple C program that prints the sum of its arguments and
reports a version string:

```c
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    if (argc > 1 && strcmp(argv[1], "--version") == 0) {
        fprintf(stderr, "Version 0.1.1\n");
        return 0;
    }
    if (argc != 2 + 1) return 1;
    printf("%d", atoi(argv[1]) + atoi(argv[2]));
}
```

Create a `test.yml` file describing the desired behaviour:

```yaml
version: 1
tests:
  - name: Arguments check
    tests:
      - name: No errors if two arguments
        args: [1, 2]
        exit: 0
      - name: Error if less than two arguments
        args: [1]
        exit: 1
  - name: Stdout is the sum of arguments
    args: [1, 2]
    stdout:
      - equals: "3"
  - name: Version on stderr
    args: ['--version']
    stderr:
      - match: 'm/\b\d\.\d\.\d\b/'
      - contains: 'Version'
```

Compile your program and run the test suite:

```console
$ cc app.c -o a.out
$ baygon -v ./a.out
Test 1: Arguments check
  Test 1.1: No errors if two arguments.......... PASSED
  Test 1.2: Error if less than two arguments.... PASSED
Test 2: Stdout is the sum of arguments.......... PASSED
Test 3: Version on stderr....................... PASSED

Ran 4 tests in 0.01s.

ok.
```

Baygon automatically detects the test file in the working directory (`test.yml`, `test.yaml`,
`test.json`, …) and executes each test sequentially.

## Documentation

The full documentation, including the DSL reference, scripting tips, and advanced configuration
guides, lives at <https://heig-tin-info.github.io/baygon/>.

## Development

Baygon uses [uv](https://docs.astral.sh/uv/) to manage development environments. Create a virtual
environment and install all dependencies (including documentation and testing extras) with:

```bash
uv venv
source .venv/bin/activate
uv sync --all-extras --group dev
```

### Local documentation preview

```bash
uv run mkdocs serve
```

### Tests and coverage

```bash
uv run pytest
```

The default pytest configuration collects coverage reports with `pytest-cov`. You can inspect the
HTML report by running `uv run pytest --cov-report html` and opening `htmlcov/index.html`.

## License

Baygon is released under the [MIT License](LICENSE).

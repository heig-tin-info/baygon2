# Baygon

**K**ills **B**ugs **D**ead!

<img src="https://github.com/heig-tin-info/baygon/raw/master/docs/docs/.vuepress/public/baygon.svg" data-canonical-src="https://github.com/heig-tin-info/baygon/docs/docs/.vuepress/public/baygon.svg" width="400"/>

This package is a minimalist functional test suite for binaries. It relies on a description of tests usually in `test.yml` or `test.json`.

The **documentation** is available [here](https://heig-tin-info.github.io/baygon/).

## Build

### Documentation

```bash
uv venv && source .venv/bin/activate
uv sync
uv run python -mmkdocs serve
```

### Tests

To run the automated test suite with [uv](https://docs.astral.sh/uv/), install the
development dependencies and invoke `pytest` via uv:

```bash
uv sync
uv run --group dev pytest
```

The `dev` dependency group matches the optional `[project.optional-dependencies.dev]`
extras declared in `pyproject.toml`, so the tests use the same toolchain as the
development environment.

"""Pytest configuration helpers for the test suite."""

from __future__ import annotations


def pytest_addoption(parser):
    """Register coverage options when pytest-cov is unavailable.

    The project configures ``--cov`` flags in ``pyproject.toml`` so local
    development automatically produces coverage reports.  The CI environment
    used for these kata-style exercises does not install ``pytest-cov`` though,
    which previously made pytest abort with ``unrecognized arguments``.  We
    register lightweight placeholders for the relevant options when the plugin
    cannot be imported so pytest accepts the flags and the real tests can run.
    """

    try:
        import pytest_cov  # noqa: F401
    except ImportError:
        parser.addoption("--cov", action="append", default=[], help="dummy option")
        parser.addoption(
            "--cov-report", action="append", default=[], help="dummy option"
        )


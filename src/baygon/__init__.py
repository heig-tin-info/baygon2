"""Top level package for Baygon."""

from __future__ import annotations

from importlib import metadata

from .filters import add_filter, get_filter, iter_filters, registry
from .matchers import add_matcher, build_matcher, get_matcher, iter_matchers, registry as matcher_registry

try:
    __version__ = metadata.version("baygon")
except metadata.PackageNotFoundError:  # pragma: no cover - used in editable installs
    __version__ = "0.0.0"

__all__ = [
    "__version__",
    "add_filter",
    "get_filter",
    "iter_filters",
    "registry",
    "add_matcher",
    "build_matcher",
    "get_matcher",
    "iter_matchers",
    "matcher_registry",
]


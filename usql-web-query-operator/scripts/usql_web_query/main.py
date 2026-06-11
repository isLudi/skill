"""Compatibility module for package execution."""

from __future__ import annotations

from usql_web_query.cli import main


if __name__ == "__main__":
    raise SystemExit(main())

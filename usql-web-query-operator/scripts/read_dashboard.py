#!/usr/bin/env python3
"""Thin wrapper: delegates to the read_dashboard package."""

from __future__ import annotations

from read_dashboard.cli import main


if __name__ == "__main__":
    raise SystemExit(main())

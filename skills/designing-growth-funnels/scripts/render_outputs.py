#!/usr/bin/env python3
"""Backward-compatible wrapper for render_final.py."""

from __future__ import annotations

from render_final import main


if __name__ == "__main__":
    raise SystemExit(main())

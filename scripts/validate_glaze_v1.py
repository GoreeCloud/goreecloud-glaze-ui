#!/usr/bin/env python3
"""Validate the current Glaze UI Stable authority and shared integrity guards.

This entrypoint is intentionally version-neutral for historical workflows. It
must validate the repository's *current* Stable authority instead of pinning an
older release as globally current. Historical V1.2 workflows call this helper
before their release-specific checks, so keeping it aligned with live lifecycle
authority prevents retired global-state assumptions from blocking newer work.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from validate_consumer_summary import main as validate_consumer_summary
from validate_css_import_closure import main as validate_css_import_closure

ROOT = Path(__file__).resolve().parents[1]


def validate_current_stable() -> int:
    completed = subprocess.run(
        ["node", str(ROOT / "scripts/verify_glaze_v1_4_stable.mjs")],
        cwd=ROOT,
        check=False,
    )
    return completed.returncode


def main() -> int:
    stable_result = validate_current_stable()
    if stable_result:
        return stable_result
    consumer_result = validate_consumer_summary()
    if consumer_result:
        return consumer_result
    return validate_css_import_closure()


if __name__ == "__main__":
    raise SystemExit(main())

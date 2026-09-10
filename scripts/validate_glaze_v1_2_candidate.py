#!/usr/bin/env python3
"""Validate retained V1.2 Candidate-era source under current Stable authority.

The deep V1.2 Candidate validator is intentionally preserved as historical
source evidence. Current lifecycle truth is validated by the shared promoted-
source runner before the legacy assertions execute against an ephemeral
historical projection.
"""
from glaze_v1_2_promoted_source_runner import run_legacy_promoted_source


def main() -> int:
    return run_legacy_promoted_source("validate_glaze_v1_2_candidate_legacy.py")


if __name__ == "__main__":
    raise SystemExit(main())

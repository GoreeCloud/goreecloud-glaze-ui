#!/usr/bin/env python3
"""Validate the historical V1.1->V1.2 migration plane under V1.2 Stable authority."""
from glaze_v1_2_promoted_source_runner import run_legacy_promoted_source

if __name__ == "__main__":
    raise SystemExit(run_legacy_promoted_source("validate_glaze_v1_2_migration_legacy.py"))

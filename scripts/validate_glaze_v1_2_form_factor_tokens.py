#!/usr/bin/env python3
"""Validate frozen V1.2 form-factor source under V1.2 Stable authority."""
from glaze_v1_2_promoted_source_runner import run_legacy_promoted_source

if __name__ == "__main__":
    raise SystemExit(run_legacy_promoted_source("validate_glaze_v1_2_form_factor_tokens_legacy.py"))

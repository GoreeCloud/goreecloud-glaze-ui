#!/usr/bin/env python3
"""Validate current GLAZE UI Stable authority and planned-next boundaries."""
from validate_consumer_summary import main as validate_consumer_summary
from validate_css_import_closure import main as validate_css_import_closure
from validate_glaze_v1_3_planned import main as validate_v1_3_release_boundary
from validate_glaze_v1_3_stable_readiness import main as validate_current_stable


def main() -> int:
    stable_result = validate_current_stable()
    if stable_result:
        return stable_result
    boundary_result = validate_v1_3_release_boundary()
    if boundary_result:
        return boundary_result
    consumer_result = validate_consumer_summary()
    if consumer_result:
        return consumer_result
    return validate_css_import_closure()


if __name__ == "__main__":
    raise SystemExit(main())

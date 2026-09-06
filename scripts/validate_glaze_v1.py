#!/usr/bin/env python3
"""Current GLAZE UI validator with Stable, consumer-summary, and corrective patch gates."""
from validate_consumer_summary import main as validate_consumer_summary
from validate_css_import_closure import main as validate_css_import_closure
from validate_glaze_v1_1_patch_candidate import main as validate_patch_candidate
from validate_glaze_v1_1_stable import main as validate_stable


def main() -> int:
    stable_result = validate_stable()
    if stable_result:
        return stable_result
    consumer_result = validate_consumer_summary()
    if consumer_result:
        return consumer_result
    closure_result = validate_css_import_closure()
    if closure_result:
        return closure_result
    return validate_patch_candidate()


if __name__ == "__main__":
    raise SystemExit(main())

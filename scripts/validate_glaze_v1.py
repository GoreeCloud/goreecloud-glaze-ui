#!/usr/bin/env python3
"""Current GLAZE UI validator for the V1.1 maintenance Stable package."""
from validate_consumer_summary import main as validate_consumer_summary
from validate_css_import_closure import main as validate_css_import_closure
from validate_glaze_v1_1_patch_stable import main as validate_stable


def main() -> int:
    stable_result = validate_stable()
    if stable_result:
        return stable_result
    consumer_result = validate_consumer_summary()
    if consumer_result:
        return consumer_result
    return validate_css_import_closure()


if __name__ == "__main__":
    raise SystemExit(main())

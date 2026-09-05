#!/usr/bin/env python3
"""Current GLAZE UI product validator for Stable authority and consumer-summary sync."""
from validate_consumer_summary import main as validate_consumer_summary
from validate_glaze_v1_1_stable import main as validate_stable


def main() -> int:
    stable_result = validate_stable()
    if stable_result != 0:
        return stable_result
    return validate_consumer_summary()


if __name__ == "__main__":
    raise SystemExit(main())

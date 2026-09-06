#!/usr/bin/env python3
"""Fail closed when the human consumer summary drifts from V1 lifecycle authority."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    lifecycle = json.loads((ROOT / "registry/lifecycle.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "consumers/registry.json").read_text(encoding="utf-8"))
    summary = (ROOT / "CONSUMERS.md").read_text(encoding="utf-8")

    version = lifecycle.get("currentStable")
    label = lifecycle.get("officialProductLabel")
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(version == registry.get("officialBaseline"), "consumer registry baseline must equal lifecycle currentStable")
    require(version == registry.get("requiredConsumerVersion"), "consumer registry required version must equal lifecycle currentStable")
    require(label == registry.get("officialProductLabel"), "consumer registry product label must equal lifecycle authority")
    require(bool(version) and bool(label), "lifecycle must declare a current Stable version and product label")

    if version and label:
        require(f"# {label} Consumers" in summary, "CONSUMERS.md heading must identify the current Stable product label")
        require(f"**{label}** (`{version}`)" in summary, "CONSUMERS.md must identify the current Stable required consumer target")
        require("Fresh repository-local" in summary, "CONSUMERS.md must preserve repository-local adoption gating")
        require("No consumer is production-eligible merely because" in summary, "CONSUMERS.md must preserve non-automatic production eligibility")

    stale_markers = (
        "GLAZE UI V1.0 (`1.0.0`)",
        "current Stable production baseline is 2.",
    )
    for marker in stale_markers:
        require(marker not in summary, f"CONSUMERS.md contains stale baseline marker: {marker}")

    if errors:
        print("GLAZE UI consumer-summary validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"GLAZE UI consumer summary: PASS ({label} / {version})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate the frozen V1.2 Candidate source layer under V1.2 Stable authority.

V1.2 Stable intentionally freezes the implementation that was developed under
Candidate-suffixed source paths.  The legacy validator contains the deep source
assertions for that implementation, but it also encoded the old global release
state (V1.1 current Stable / V1.2 active Candidate).  After promotion those
release-state assertions are historical, not current authority.

This harness therefore validates the real Stable lifecycle first, then runs the
legacy source validator against an in-memory historical lifecycle projection.
The projection exists only so the legacy validator can exercise its unchanged
source assertions; it is never written to the repository and is not release
evidence.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY_PATH = ROOT / "scripts/validate_glaze_v1_2_candidate_legacy.py"
LIFECYCLE_PATH = ROOT / "registry/lifecycle.json"


def req(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"GLAZE UI V1.2 promoted-source validation failed: {message}")


def load_json(path: Path) -> dict:
    req(path.is_file(), f"missing required file: {path.relative_to(ROOT)}")
    data = json.loads(path.read_text(encoding="utf-8"))
    req(isinstance(data, dict), f"expected JSON object: {path.relative_to(ROOT)}")
    return data


def validate_live_stable_lifecycle(lifecycle: dict) -> None:
    req(lifecycle.get("officialProductLabel") == "GLAZE UI V1.2", "official product label must remain GLAZE UI V1.2")
    req(lifecycle.get("currentStable") == "1.2.0", "currentStable must remain 1.2.0")
    req(lifecycle.get("currentOfficial") == "1.2.0", "currentOfficial must remain 1.2.0")
    req(lifecycle.get("activeCandidate") is None, "V1.2 Stable must not remain registered as an active Candidate")
    req(lifecycle.get("plannedNext") == "1.3.0-candidate", "plannedNext must remain the V1.3 Candidate track")

    release = next(
        (
            item
            for item in lifecycle.get("releases", [])
            if isinstance(item, dict) and item.get("version") == "1.2.0"
        ),
        None,
    )
    req(release is not None, "Stable V1.2 lifecycle record missing")
    assert release is not None
    req(release.get("status") == "stable", "V1.2 lifecycle status must remain Stable")
    req(release.get("consumerEligible") is True, "V1.2 Stable must remain consumer-adoptable")
    req(release.get("stableBaseline") == "1.1.0", "V1.2 Stable baseline must remain V1.1")
    req(release.get("contract") == "GLAZE_UI_V1_2.md", "V1.2 Stable contract binding drifted")

    capability = lifecycle.get("capabilities", {}).get("frosted-neutral-system-shell", {})
    req(capability.get("status") == "stable-promoted-source", "System Shell promoted-source status drifted")
    req(capability.get("since") == "1.2.0", "System Shell Stable capability version drifted")
    req(
        capability.get("implementation") == "contracts/v1.2/system-shell-materials.candidate.json",
        "System Shell promoted-source implementation binding drifted",
    )
    req(
        capability.get("webPreview") == "reference/v1.2/system-shell.html",
        "System Shell promoted-source preview binding drifted",
    )


def historical_candidate_projection(lifecycle: dict) -> dict:
    """Return the minimum historical lifecycle fixture required by the legacy validator."""
    projected = copy.deepcopy(lifecycle)
    projected["officialProductLabel"] = "GLAZE UI V1.1"
    projected["currentStable"] = "1.1.0"
    projected["currentOfficial"] = "1.1.0"
    projected["activeCandidate"] = "1.2.0-candidate"

    releases = [
        item
        for item in projected.get("releases", [])
        if not (isinstance(item, dict) and item.get("version") == "1.2.0-candidate")
    ]
    releases.append(
        {
            "version": "1.2.0-candidate",
            "label": "GLAZE UI V1.2 — Frosted Neutral Candidate",
            "status": "candidate",
            "consumerEligible": False,
            "stableBaseline": "1.1.0",
            "contract": "GLAZE_UI_V1_2_CANDIDATE.md",
        }
    )
    projected["releases"] = releases

    capabilities = projected.setdefault("capabilities", {})
    shell = copy.deepcopy(capabilities.get("frosted-neutral-system-shell", {}))
    shell["status"] = "candidate"
    shell["since"] = "1.2.0-candidate"
    shell["implementation"] = "contracts/v1.2/system-shell-materials.candidate.json"
    shell["webPreview"] = "reference/v1.2/system-shell.html"
    capabilities["frosted-neutral-system-shell"] = shell
    return projected


def run_legacy_source_validation(projected_lifecycle: dict) -> None:
    req(LEGACY_PATH.is_file(), "historical Candidate source validator is missing")
    spec = importlib.util.spec_from_file_location("glaze_v1_2_candidate_legacy", LEGACY_PATH)
    req(spec is not None and spec.loader is not None, "could not load historical Candidate source validator")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json") as handle:
        json.dump(projected_lifecycle, handle, indent=2)
        handle.flush()
        module.LIFECYCLE_PATH = Path(handle.name)
        module.main()


def main() -> int:
    lifecycle = load_json(LIFECYCLE_PATH)
    validate_live_stable_lifecycle(lifecycle)
    run_legacy_source_validation(historical_candidate_projection(lifecycle))
    print("GLAZE UI V1.2 promoted Candidate source validation: PASS")
    print("Authority: live lifecycle is Stable 1.2.0; Candidate-era lifecycle fields are historical test-fixture data only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

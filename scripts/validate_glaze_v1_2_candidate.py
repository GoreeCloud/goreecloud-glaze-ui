#!/usr/bin/env python3
"""Validate the frozen V1.2 promoted-source layer without pinning global authority.

V1.2 remains a retained historical Stable release after newer Glaze UI releases
become current. The deep legacy validator still expects the Candidate-era
lifecycle shape that existed before V1.2 promotion, so this wrapper verifies the
live lifecycle truth first and then supplies an in-memory historical projection
only to exercise those unchanged V1.2 source assertions.

The historical projection is test-fixture data only. It is never written back to
the repository and must never replace current lifecycle authority.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import re
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


def release_for(lifecycle: dict, version: str) -> dict | None:
    return next(
        (
            item
            for item in lifecycle.get("releases", [])
            if isinstance(item, dict) and item.get("version") == version
        ),
        None,
    )


def validate_live_stable_lifecycle(lifecycle: dict) -> None:
    """Validate current global authority plus the retained V1.2 release record.

    A historical-release validator must not require V1.2 to remain the global
    current Stable after V1.3/V1.4 promotion. It instead verifies that the live
    current pointers are internally coherent and that V1.2's immutable Stable
    record and source bindings remain intact.
    """
    current_stable = lifecycle.get("currentStable")
    current_official = lifecycle.get("currentOfficial")
    req(isinstance(current_stable, str) and current_stable, "currentStable must identify a live Stable release")
    req(current_official == current_stable, "currentOfficial must match currentStable")

    current_release = release_for(lifecycle, current_stable)
    req(current_release is not None, "currentStable does not resolve to a lifecycle release")
    assert current_release is not None
    req(current_release.get("status") == "stable", "currentStable lifecycle record must be Stable")
    req(current_release.get("consumerEligible") is True, "currentStable release must remain consumer-eligible")
    req(
        lifecycle.get("officialProductLabel") == current_release.get("label"),
        "officialProductLabel must match the current Stable release label",
    )

    release = release_for(lifecycle, "1.2.0")
    req(release is not None, "retained Stable V1.2 lifecycle record missing")
    assert release is not None
    req(release.get("status") == "stable", "V1.2 lifecycle status must remain Stable")
    req(release.get("consumerEligible") is True, "V1.2 retained Stable must remain consumer-adoptable")
    req(release.get("stableBaseline") == "1.1.0", "V1.2 Stable baseline must remain V1.1")
    req(release.get("contract") == "GLAZE_UI_V1_2.md", "V1.2 Stable contract binding drifted")
    req(release.get("webEntrypoint") == "css/glaze-v1.2.0.css", "V1.2 web entrypoint binding drifted")
    req(release.get("runtimeEntrypoint") == "js/glaze-v1.2.0.mjs", "V1.2 runtime entrypoint binding drifted")
    req(release.get("reference") == "reference/v1.2/frosted-neutral.html", "V1.2 reference binding drifted")
    req(
        release.get("opticalFoundation") == "tokens/glaze-v1.2-optical-foundation.candidate.json",
        "V1.2 optical foundation binding drifted",
    )
    anchor = release.get("sourceQualificationAnchor")
    req(
        isinstance(anchor, str) and re.fullmatch(r"[0-9a-f]{40}", anchor) is not None,
        "V1.2 source qualification anchor must remain a 40-character commit SHA",
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

    # The legacy helper deliberately rejects paths outside ROOT. Place the
    # ephemeral lifecycle fixture inside the checkout, then let
    # NamedTemporaryFile remove it immediately after validation.
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        suffix=".json",
        prefix=".glaze-v1.2-historical-lifecycle-",
        dir=ROOT,
    ) as handle:
        json.dump(projected_lifecycle, handle, indent=2)
        handle.flush()
        module.LIFECYCLE_PATH = Path(handle.name)
        module.main()


def main() -> int:
    lifecycle = load_json(LIFECYCLE_PATH)
    validate_live_stable_lifecycle(lifecycle)
    run_legacy_source_validation(historical_candidate_projection(lifecycle))
    print("GLAZE UI V1.2 retained promoted-source validation: PASS")
    print(
        "Authority: current global Stable lifecycle is verified independently; "
        "V1.2 Candidate-era lifecycle fields are historical test-fixture data only."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

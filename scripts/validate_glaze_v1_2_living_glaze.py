#!/usr/bin/env python3
"""Validate the bounded GLAZE UI V1.2 Living Frosted Candidate tranche."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "1.2.0-candidate"
EXPECTED_STABLE = "1.1.0"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(f"Glaze V1.2 Living Glaze validation failed: {message}")


def load(path: str):
    p = ROOT / path
    require(p.is_file(), f"missing {path}")
    return json.loads(p.read_text(encoding="utf-8"))


def text(path: str) -> str:
    p = ROOT / path
    require(p.is_file(), f"missing {path}")
    return p.read_text(encoding="utf-8")


def main() -> int:
    require(text("VERSION").strip() == EXPECTED_STABLE, "VERSION moved away from Stable 1.1.0")
    lifecycle = load("registry/lifecycle.json")
    require(lifecycle.get("currentStable") == EXPECTED_STABLE, "currentStable drifted")
    require(lifecycle.get("currentOfficial") == EXPECTED_STABLE, "currentOfficial drifted")
    require(lifecycle.get("activeCandidate") == EXPECTED_VERSION, "activeCandidate drifted")
    candidate = next((r for r in lifecycle.get("releases", []) if r.get("version") == EXPECTED_VERSION), None)
    require(candidate is not None and candidate.get("status") == "candidate", "Candidate lifecycle entry missing")
    require(candidate.get("consumerEligible") is False, "Candidate became consumer eligible")

    contract = load("contracts/v1.2/living-glaze.candidate.json")
    require(contract.get("version") == EXPECTED_VERSION, "contract version drifted")
    require(contract.get("lifecycle") == "candidate", "contract lifecycle drifted")
    require(contract.get("consumerEligible") is False, "contract became consumer eligible")
    require(contract.get("stableBaseline") == EXPECTED_STABLE, "Stable baseline drifted")
    require(contract.get("theme") == "Living Frosted", "theme identity drifted")
    require(contract.get("interactionStates") == ["rest","hover","focus","pressed","dragged","selected","expanded","loading","disabled"], "interaction state set drifted")
    require(list(contract.get("clarityProfiles", {}).keys()) == ["clear","balanced","dense"], "clarity profiles drifted")
    tiers = contract.get("performanceTiers", {})
    require(tiers.get("degradationOrder") == [3,2,1,0], "performance fallback order drifted")
    require(contract.get("stableCompatibleMotion", {}).get("experimentalGlazeMotionRequired") is False, "Experimental Glaze Motion became required")
    require("no-unrestricted-image-analysis" in contract.get("opticalResponse", {}).get("privacyBoundary", ""), "privacy boundary weakened")

    material = load("tokens/glaze-v1.2-living-material.candidate.json")
    require(list(material.get("clarity", {}).keys()) == ["clear","balanced","dense"], "material clarity tokens drifted")
    require(material.get("performanceTiers") == {"0":"solid","1":"static-glaze","2":"responsive-glaze","3":"living-glaze"}, "material tier tokens drifted")
    ergonomics = load("tokens/glaze-v1.2-ergonomics.candidate.json")
    require(ergonomics.get("targets", {}).get("touchMinimumPx") == 48, "touch target floor weakened")
    require(ergonomics.get("targets", {}).get("touchAssistanceMinimumPx") == 56, "Touch Assistance target floor weakened")
    require(ergonomics.get("viewportWidthAloneDeterminesIntent") is False, "viewport width became sole intent proxy")

    css = text("css/glaze-v1.2-living-glaze.candidate.css")
    for marker in ('data-glaze-clarity="clear"','data-glaze-clarity="dense"','data-material-state="pressed"','data-material-state="dragged"','data-glaze-navigation-capsule','prefers-reduced-motion','forced-colors','data-glaze-tier="0"'):
        require(marker in css, f"CSS marker missing: {marker}")
    runtime = text("js/glaze-v1.2-living-glaze.candidate.mjs")
    for export in ("setGlazeClarity", "setLivingGlazeState", "setBackdropComplexity", "setGlazeComplexityTier", "connectMaterialTransformation"):
        require(f"export function {export}" in runtime, f"runtime export missing: {export}")
    require("producer-or-renderer-supplied-complexity-only" in runtime, "runtime privacy boundary missing")

    reference = text("reference/v1.2/living-glaze.html")
    for marker in ("Living Glaze Material Lab", "Simple backdrop", "Complex backdrop", "Fail closed", "Adaptive Navigation Capsule"):
        require(marker in reference, f"reference marker missing: {marker}")
    entry = text("css/glaze-v1.2.0-candidate.css")
    require('glaze-v1.2-living-glaze.candidate.css' in entry, "aggregate Candidate CSS does not import Living Glaze")
    spec = text("GLAZE_UI_V1_2_CANDIDATE.md")
    require("Living Frosted extended Candidate" in spec, "Candidate specification does not bind Living Frosted extension")

    print("GLAZE UI V1.2 Living Frosted Candidate tranche validated; Stable 1.1.0 authority preserved; no RC, Stable, human, native, or consumer acceptance implied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

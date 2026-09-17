#!/usr/bin/env python3
"""Validate retained GLAZE UI V1.2 Stable source without claiming current authority.

V1.2 remains an immutable historical Stable release after later Glaze releases
become current. This check validates that retained release record and its frozen
source bindings while separately requiring live lifecycle/VERSION coherence.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RETAINED_VERSION = "1.2.0"


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def release_for(lifecycle: dict, version: str):
    return next(
        (item for item in lifecycle.get("releases", []) if isinstance(item, dict) and item.get("version") == version),
        None,
    )


def current_family_prefix(version: str) -> str | None:
    """Return the marketing-family prefix for a semantic release version.

    ``officialProductLabel`` is intentionally a family-level product label (for
    example ``GLAZE UI V1.5 — ...``), while ``currentStable`` can advance through
    patch releases such as 1.5.1. A retained-release validator must therefore
    verify family coherence without requiring the family label to equal the
    patch release's own release-specific label.
    """

    match = re.fullmatch(r"(\d+)\.(\d+)\.\d+(?:[-+][0-9A-Za-z.-]+)?", version)
    if not match:
        return None
    return f"GLAZE UI V{match.group(1)}.{match.group(2)}"


def main() -> int:
    errors: list[str] = []

    def req(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    lifecycle = load("registry/lifecycle.json")
    live_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    current_stable = lifecycle.get("currentStable")
    current_official = lifecycle.get("currentOfficial")

    req(isinstance(current_stable, str) and bool(current_stable), "currentStable must identify a live release")
    req(live_version == current_stable, "VERSION must match live currentStable")
    req(current_official == current_stable, "currentOfficial must match live currentStable")

    current = release_for(lifecycle, current_stable) if isinstance(current_stable, str) else None
    req(bool(current) and current.get("status") == "stable", "live currentStable record must be Stable")
    req(bool(current) and current.get("consumerEligible") is True, "live currentStable record must be consumer-eligible")

    family_prefix = current_family_prefix(current_stable) if isinstance(current_stable, str) else None
    official_label = lifecycle.get("officialProductLabel")
    req(family_prefix is not None, "currentStable must be a semantic release version")
    req(
        isinstance(official_label, str)
        and bool(official_label.strip())
        and family_prefix is not None
        and official_label.startswith(family_prefix),
        "officialProductLabel must identify the live currentStable product family",
    )

    retained = release_for(lifecycle, RETAINED_VERSION)
    req(bool(retained) and retained.get("status") == "stable", "retained lifecycle must contain Stable 1.2.0")
    req(bool(retained) and retained.get("consumerEligible") is True, "retained V1.2 must remain consumer-adoptable as a historical Stable release")
    req(bool(retained) and retained.get("stableBaseline") == "1.1.0", "retained V1.2 rollback baseline must remain 1.1.0")
    req(bool(retained) and retained.get("contract") == "GLAZE_UI_V1_2.md", "retained V1.2 contract binding drifted")
    req(bool(retained) and retained.get("webEntrypoint") == "css/glaze-v1.2.0.css", "retained V1.2 web entrypoint binding drifted")
    req(bool(retained) and retained.get("runtimeEntrypoint") == "js/glaze-v1.2.0.mjs", "retained V1.2 runtime entrypoint binding drifted")
    anchor = retained.get("sourceQualificationAnchor") if retained else None
    req(isinstance(anchor, str) and re.fullmatch(r"[0-9a-f]{40}", anchor or "") is not None, "retained V1.2 sourceQualificationAnchor must be a 40-character SHA")

    required = (
        "GLAZE_UI_V1_2.md",
        "GLAZE_UI_V1_2_CANDIDATE.md",
        "css/glaze-v1.2.0.css",
        "css/glaze-v1.2.0-candidate.css",
        "js/glaze-v1.2.0.mjs",
        "acceptance/v1.2-stable.md",
        "tokens/glaze-v1.2-optical-foundation.candidate.json",
        "GLAZE_UI_V1_1.md",
        "acceptance/v1.1-stable.md",
    )
    for path in required:
        req((ROOT / path).is_file(), f"missing retained Stable authority/provenance file: {path}")

    css = (ROOT / "css/glaze-v1.2.0.css").read_text(encoding="utf-8")
    req('@import url("./glaze-v1.2.0-candidate.css")' in css, "retained V1.2 Stable CSS wrapper must freeze promoted V1.2 rendering source")
    runtime = (ROOT / "js/glaze-v1.2.0.mjs").read_text(encoding="utf-8")
    req('export * from "./glaze-v1.1.0.mjs"' in runtime, "retained V1.2 runtime must preserve inherited V1 runtime")
    req("glaze-v1.2-living-glaze.candidate.mjs" in runtime, "retained V1.2 runtime must export Living Glaze")
    req("glaze-v1.2-personalization.candidate.mjs" in runtime, "retained V1.2 runtime must export Personalization")

    acceptance = (ROOT / "acceptance/v1.2-stable.md").read_text(encoding="utf-8")
    req("V1.2" in acceptance and "Stable" in acceptance, "retained V1.2 acceptance provenance lost release identity")

    if errors:
        print("GLAZE UI V1.2 retained Stable source validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GLAZE UI V1.2 retained Stable source authority: PASS")
    print(f"Live current Stable remains {current_stable}; retained V1.2 provenance does not override current authority.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

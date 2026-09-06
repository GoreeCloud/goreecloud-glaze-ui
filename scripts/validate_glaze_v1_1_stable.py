#!/usr/bin/env python3
"""Validate preserved GLAZE UI V1.1 Stable rollback/source integrity under V1.2."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V11_VERSION = "1.1.0"
V11_PRODUCT = "GLAZE UI V1.1"
LIVE_VERSION = "1.2.0"
LIVE_PRODUCT = "GLAZE UI V1.2"
STABLE_ACTIVATION = 'html[data-glaze-version="1.1"]'
CANDIDATE_ACTIVATION = 'html[data-glaze-version-candidate="1.1"]'


def load(path: str):
    with (ROOT / path).open(encoding="utf-8") as handle:
        return json.load(handle)


def stable_optical(candidate: str) -> str:
    candidate = re.sub(
        r"\A/\*.*?\*/\n",
        "/*\n * GLAZE UI V1.1 — Stable optical refinement layer.\n * Activation: html[data-glaze-version=\\\"1.1\\\"] only.\n * Inherits the GLAZE UI V1.0 structural material baseline without adding\n * nested backdrop blur, semantic-state authority, content sampling, or remote assets.\n */\n",
        candidate,
        count=1,
        flags=re.DOTALL,
    )
    candidate = candidate.replace('@import url("./glaze-v1.0.0.css");\n\n', "", 1)
    return candidate.replace(CANDIDATE_ACTIVATION, STABLE_ACTIVATION)


def stable_appearance(candidate: str) -> str:
    candidate = re.sub(
        r"\A/\*.*?\*/\n",
        "/*\n * GLAZE UI V1.1 — Stable explicit appearance adapter.\n * Maps Light, Dark, and Deep Dark to inherited V1 structural surface/text roles.\n * Protected semantic-state colors remain producer-authoritative and unchanged.\n */\n",
        candidate,
        count=1,
        flags=re.DOTALL,
    )
    return candidate.replace(CANDIDATE_ACTIVATION, STABLE_ACTIVATION)


def main() -> int:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    # Live product authority is V1.2; this validator protects the prior Stable
    # rollback/source package and must never move current lifecycle state backward.
    require((ROOT / "VERSION").read_text(encoding="utf-8").strip() == LIVE_VERSION,
            "live VERSION must remain V1.2 / 1.2.0")
    lifecycle = load("registry/lifecycle.json")
    require(lifecycle.get("officialProductLabel") == LIVE_PRODUCT,
            "live lifecycle official product must remain GLAZE UI V1.2")
    require(lifecycle.get("currentOfficial") == LIVE_VERSION,
            "live lifecycle currentOfficial must remain 1.2.0")
    require(lifecycle.get("currentStable") == LIVE_VERSION,
            "live lifecycle currentStable must remain 1.2.0")
    release = next((item for item in lifecycle.get("releases", []) if item.get("version") == V11_VERSION), None)
    require(bool(release) and release.get("status") == "stable",
            "lifecycle must retain the prior Stable 1.1.0 release")
    require(bool(release) and release.get("consumerEligible") is True,
            "V1.1 rollback release record must retain its historical consumer eligibility")
    live_release = next((item for item in lifecycle.get("releases", []) if item.get("version") == LIVE_VERSION), None)
    require(bool(live_release) and live_release.get("status") == "stable" and live_release.get("consumerEligible") is True,
            "live V1.2 Stable release record drifted")

    for path in (
        "GLAZE_UI_V1_1.md",
        "contracts/v1.1/optical-refinement.json",
        "tokens/glaze-v1.1-atmosphere.json",
        "css/glaze-v1.1.css",
        "css/glaze-v1.1-appearance.css",
        "css/glaze-v1.1.0.css",
        "js/glaze-v1.1.0.mjs",
        "acceptance/v1.1-stable.md",
        "contracts/v1.1/release.json",
    ):
        require((ROOT / path).is_file(), f"missing preserved Stable V1.1 rollback artifact: {path}")

    stable_contract = load("contracts/v1.1/optical-refinement.json")
    require(stable_contract.get("product") == V11_PRODUCT and stable_contract.get("version") == V11_VERSION,
            "V1.1 Stable optical contract identity mismatch")
    require(stable_contract.get("lifecycle") == "stable", "V1.1 Stable optical contract lifecycle mismatch")
    boundary = stable_contract.get("releaseBoundary", {})
    require(boundary.get("currentTarget") is True,
            "historical V1.1 Stable optical contract must preserve its promotion-time currentTarget record")
    require(boundary.get("downstreamConsumerConformanceAutomatic") is False,
            "V1.1 Stable source must not auto-conform consumers")

    atmosphere = load("tokens/glaze-v1.1-atmosphere.json")
    require(atmosphere.get("product") == V11_PRODUCT and atmosphere.get("version") == V11_VERSION,
            "V1.1 Stable atmosphere identity mismatch")
    require(atmosphere.get("lifecycle") == "stable" and atmosphere.get("currentV1Token") is True,
            "V1.1 promoted atmosphere source lifecycle mismatch")
    require(atmosphere.get("primitives", {}).get("deepTeal") == "#0F6B6F", "Deep Teal primitive drift")
    require(atmosphere.get("primitives", {}).get("softAmber") == "#D9A35F", "Soft Amber primitive drift")
    require(atmosphere.get("semanticPrecedence", {}).get("atmosphereIsLowestPriority") is True,
            "V1.1 atmosphere must remain lowest priority")

    stable_css = (ROOT / "css/glaze-v1.1.css").read_text(encoding="utf-8")
    stable_appearance_css = (ROOT / "css/glaze-v1.1-appearance.css").read_text(encoding="utf-8")
    candidate_css = (ROOT / "css/glaze-v1.1-candidate.css").read_text(encoding="utf-8")
    candidate_appearance = (ROOT / "css/glaze-v1.1-appearance.candidate.css").read_text(encoding="utf-8")
    require(stable_css.rstrip() == stable_optical(candidate_css).rstrip(),
            "V1.1 Stable optical CSS must remain deterministic promotion of approved Candidate CSS")
    require(stable_appearance_css.rstrip() == stable_appearance(candidate_appearance).rstrip(),
            "V1.1 Stable appearance CSS must remain deterministic promotion of approved Candidate adapter")
    require(CANDIDATE_ACTIVATION not in stable_css and STABLE_ACTIVATION in stable_css,
            "V1.1 Stable optical CSS activation namespace mismatch")
    require(CANDIDATE_ACTIVATION not in stable_appearance_css and STABLE_ACTIVATION in stable_appearance_css,
            "V1.1 Stable appearance activation namespace mismatch")
    require("backdrop-filter" not in stable_css.lower(), "V1.1 Stable optical layer must not add nested backdrop filtering")
    require("@keyframes" not in stable_css.lower(), "V1.1 Stable optical layer must not add decorative keyframes")
    require("http://" not in stable_css.lower() and "https://" not in stable_css.lower(),
            "V1.1 Stable optical layer must not depend on remote assets")

    entry = (ROOT / "css/glaze-v1.1.0.css").read_text(encoding="utf-8")
    for marker in ('@import url("./glaze-v1.0.0.css")', '@import url("./glaze-v1.1.css")', '@import url("./glaze-v1.1-appearance.css")'):
        require(marker in entry, f"V1.1 Stable web entrypoint missing {marker}")
    runtime = (ROOT / "js/glaze-v1.1.0.mjs").read_text(encoding="utf-8")
    require('export * from "./glaze-v1.runtime.mjs"' in runtime,
            "V1.1 Stable runtime must preserve V1 runtime export")
    require('export * from "./glaze-v1.system-interactions.mjs"' in runtime,
            "V1.1 Stable runtime must preserve V1 system interaction export")

    baseline = load("contracts/regression/visual-baselines-v1.json")
    require(baseline.get("product") == V11_PRODUCT and baseline.get("version") == V11_VERSION,
            "preserved V1.1 visual baseline identity mismatch")
    require(baseline.get("status") == "stable-human-approved-source-pinned",
            "V1.1 visual baseline must remain human-approved and source-pinned")
    require(len(baseline.get("cases", {})) == 5,
            "V1.1 visual baseline must retain five approved cases")

    # Current consumer and evidence authorities must point forward to V1.2, while
    # V1.1 remains available only as rollback/audit source.
    consumers = load("consumers/registry.json")
    require(consumers.get("officialBaseline") == LIVE_VERSION and consumers.get("requiredConsumerVersion") == LIVE_VERSION,
            "current consumer registry must require 1.2.0")
    require(consumers.get("officialProductLabel") == LIVE_PRODUCT,
            "current consumer registry product label must be GLAZE UI V1.2")
    require(all(item.get("requiredTargetVersion") == LIVE_VERSION for item in consumers.get("consumers", [])),
            "every listed current consumer must require 1.2.0")
    require(not any(item.get("productionEligible") is True for item in consumers.get("consumers", [])),
            "design-system Stable promotion must not auto-mark consumers production eligible")

    evidence_schema = load("contracts/glaze.conformance-evidence.schema.json")
    target = evidence_schema.get("properties", {}).get("target", {}).get("properties", {})
    require(target.get("glaze_version", {}).get("const") == LIVE_VERSION,
            "current conformance evidence schema must target 1.2.0")

    token_manifest = load("tokens/glaze-v1.json")
    require(token_manifest.get("product") == LIVE_PRODUCT and token_manifest.get("version") == LIVE_VERSION
            and token_manifest.get("status") == "stable",
            "current token manifest must remain V1.2 Stable")

    current_docs = {
        "README.md": (LIVE_PRODUCT, LIVE_VERSION, "current Stable"),
        "SPECIFICATIONS.md": (LIVE_PRODUCT, LIVE_VERSION, "Stable"),
        "BRANDING.md": (LIVE_PRODUCT, LIVE_VERSION, "Stable"),
        "ACCEPTANCE.md": (LIVE_PRODUCT, LIVE_VERSION, "Stable"),
        "website/index.html": (LIVE_PRODUCT, LIVE_VERSION, "Current Stable authority"),
        "website/404.html": (LIVE_PRODUCT, LIVE_VERSION),
    }
    for path, markers in current_docs.items():
        text = (ROOT / path).read_text(encoding="utf-8")
        for marker in markers:
            require(marker in text, f"{path} missing current V1.2 authority marker {marker!r}")

    historical_v11 = (ROOT / "GLAZE_UI_V1_1.md").read_text(encoding="utf-8")
    require(V11_PRODUCT in historical_v11 and V11_VERSION in historical_v11,
            "historical V1.1 Stable contract identity missing")
    require("historical" in historical_v11[:1400].lower() or "superseded" in historical_v11[:1400].lower(),
            "V1.1 Stable contract must identify its historical/rollback status near the preamble")
    require(LIVE_PRODUCT in historical_v11[:2200] or LIVE_VERSION in historical_v11[:2200],
            "V1.1 Stable contract must point to V1.2 current authority")

    require((ROOT / "GLAZE_UI_V1_0.md").is_file(), "historical V1.0 contract must remain available for audit")
    require((ROOT / "contracts/v1.1/optical-refinement.candidate.json").is_file(),
            "V1.1 Candidate machine contract must remain as audit evidence")
    require((ROOT / "contracts/v1.1/release-candidate.rc.json").is_file(),
            "V1.1 release-candidate record must remain as audit evidence")

    if errors:
        print("GLAZE UI V1.1 rollback source validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("GLAZE UI V1.1 rollback Stable source integrity: PASS")
    print("Authority: live lifecycle remains GLAZE UI V1.2 / 1.2.0; V1.1 is preserved for rollback and audit only.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

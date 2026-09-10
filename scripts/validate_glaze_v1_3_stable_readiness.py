#!/usr/bin/env python3
"""Validate V1.3.0 Stable authority and preserve the historical Stable-readiness mechanism as V1.3.1 follow-up provenance."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STABLE = "1.3.0"


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main():
    errors = []

    def req(ok, msg):
        if not ok:
            errors.append(msg)

    required = [
        "contracts/v1.3/stable-readiness.plan.json",
        "js/glaze-v1.3-stable-readiness.candidate.mjs",
        "scripts/evaluate_glaze_v1_3_stable_readiness.mjs",
        "tests/glaze-v1.3-stable-readiness.test.mjs",
        "acceptance/v1.3-stable.md",
        "acceptance/v1.3-deferred-qualification.md",
        "GLAZE_UI_V1_3_1_HARDENING.md",
        "registry/lifecycle.json",
        "VERSION",
        "css/glaze-v1.3.0.css",
        "js/glaze-v1.3.0.mjs",
    ]
    for path in required:
        req((ROOT / path).is_file(), f"missing Stable/readiness artifact: {path}")

    if errors:
        print("GLAZE UI V1.3 Stable authority validation FAILED:")
        for e in errors:
            print(f"- {e}")
        return 1

    lifecycle = load("registry/lifecycle.json")
    req((ROOT / "VERSION").read_text().strip() == STABLE, "VERSION must be 1.3.0")
    req(lifecycle.get("currentStable") == STABLE, "currentStable must be 1.3.0")
    req(lifecycle.get("currentOfficial") == STABLE, "currentOfficial must be 1.3.0")
    req(lifecycle.get("activeCandidate") is None, "no Candidate may remain active after V1.3.0 Stable release")

    release = next((x for x in lifecycle.get("releases", []) if x.get("version") == STABLE), None)
    req(bool(release) and release.get("status") == "stable", "1.3.0 release record must be Stable")
    req(bool(release) and release.get("consumerEligible") is True, "1.3.0 must be consumer-eligible")
    req(bool(release) and release.get("acceptance") == "acceptance/v1.3-stable.md", "Stable acceptance authority mismatch")

    runtime = (ROOT / "js/glaze-v1.3-stable-readiness.candidate.mjs").read_text()
    for symbol in ["evaluateStableReadiness", "STABLE_CLEANUP_WORKSTREAM", "stableReadinessCandidate"]:
        req(symbol in runtime, f"historical Stable-readiness runtime missing API: {symbol}")
    for token in ["fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket(", "localStorage", "sessionStorage", "indexedDB", "child_process", "node:fs"]:
        req(token not in runtime, f"Stable-readiness runtime contains forbidden side-effect primitive: {token}")

    acceptance = (ROOT / "acceptance/v1.3-stable.md").read_text()
    deferred = (ROOT / "acceptance/v1.3-deferred-qualification.md").read_text()
    hardening = (ROOT / "GLAZE_UI_V1_3_1_HARDENING.md").read_text()
    req("Official Stable release" in acceptance, "Stable acceptance must be active")
    req("V1.3.1" in acceptance and "V1.3.1" in deferred and "V1.3.1" in hardening,
        "former Stable-readiness blockers must be visibly transferred to V1.3.1")
    evidence_integrity_language = (
        "must not be represented as passed" in acceptance
        and "not rewritten as a pass" in acceptance
    )
    req(evidence_integrity_language, "Stable release must not fabricate readiness evidence")

    if errors:
        print("GLAZE UI V1.3 Stable authority validation FAILED:")
        for e in errors:
            print(f"- {e}")
        return 1

    print("GLAZE UI V1.3 Stable authority: PASS")
    print("1.3.0 is Official/Stable/consumer-eligible; the historical readiness mechanism remains audit provenance and unresolved cleanup is V1.3.1 follow-up.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

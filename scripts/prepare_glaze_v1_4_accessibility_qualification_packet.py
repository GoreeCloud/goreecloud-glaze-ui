#!/usr/bin/env python3
"""Prepare fail-closed Glaze UI V1.4 accessibility qualification packets.

A prepared packet binds the evidence draft to one immutable source commit and tree,
prefills only operator-supplied environment/claim metadata, and creates a capture
checklist. It never fabricates qualification observations, human acceptance, consumer
conformance, or lifecycle promotion.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DRAFT_ROOT = (ROOT / "artifacts" / "v1.4" / "accessibility-qualification-drafts").resolve()
PLAN = ROOT / "contracts" / "v1.4" / "accessibility-qualification.candidate.json"
TEMPLATE = ROOT / "evidence" / "v1.4" / "templates" / "accessibility-qualification-record.candidate.json"
EVALUATOR = ROOT / "scripts" / "evaluate_glaze_v1_4_accessibility_qualification.py"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
ZERO_SHA = "0" * 40


class PreparationError(RuntimeError):
    pass


def req(ok: bool, message: str) -> None:
    if not ok:
        raise PreparationError(message)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreparationError(f"unable to read {path.relative_to(ROOT)}: {exc}") from exc
    req(isinstance(value, dict), f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def validate_revision(value: str, label: str) -> str:
    value = value.strip()
    req(bool(HEX40.fullmatch(value)), f"{label} must be an immutable 40-character lowercase SHA")
    req(value != ZERO_SHA, f"{label} must not be the placeholder zero SHA")
    return value


def git_revision(revision: str = "HEAD") -> str:
    try:
        value = subprocess.check_output(
            ["git", "rev-parse", revision], cwd=ROOT, text=True, stderr=subprocess.STDOUT
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise PreparationError(f"unable to resolve Git revision {revision!r}; pass exact revisions explicitly") from exc
    return validate_revision(value, "source revision")


def git_tree_revision(source_revision: str) -> str:
    source_revision = validate_revision(source_revision, "source revision")
    try:
        value = subprocess.check_output(
            ["git", "rev-parse", f"{source_revision}^{{tree}}"], cwd=ROOT, text=True, stderr=subprocess.STDOUT
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise PreparationError(
            "unable to resolve source tree revision; pass --source-tree-revision explicitly"
        ) from exc
    return validate_revision(value, "source tree revision")


def observed_at_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_evaluator():
    spec = importlib.util.spec_from_file_location("glaze_v14_accessibility_qualification_evaluator", EVALUATOR)
    req(bool(spec and spec.loader), "qualification evaluator could not be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_record(
    *,
    authority: str,
    review_mode: str,
    source_revision: str,
    source_tree_revision: str,
    platform_family: str,
    os_name: str,
    os_version: str,
    browser_name: str | None = None,
    browser_version: str | None = None,
    physical_device: bool = False,
    screen_reader_claimed: bool = False,
    voice_control_claimed: bool = False,
    switch_control_claimed: bool = False,
    observed_at: str | None = None,
) -> dict[str, Any]:
    authority = authority.strip()
    req(bool(authority), "review authority must not be empty")
    req(review_mode in {"human", "combined", "automated"}, "review mode must be human, combined, or automated")
    req(platform_family in {"web", "android", "linux", "other"}, "unsupported platform family")
    req(bool(os_name.strip()), "operating-system name must not be empty")
    req(bool(os_version.strip()), "operating-system version must not be empty")
    if bool(browser_name) != bool(browser_version):
        raise PreparationError("browser name and browser version must be supplied together")

    source_revision = validate_revision(source_revision, "source revision")
    source_tree_revision = validate_revision(source_tree_revision, "source tree revision")
    record = copy.deepcopy(load_json(TEMPLATE))
    record["target"]["sourceRevision"] = source_revision
    record["target"]["sourceTreeRevision"] = source_tree_revision
    record["status"] = "in-progress"
    record["observedAt"] = observed_at or observed_at_now()
    record["reviewAuthority"] = {
        "mode": review_mode,
        "authority": authority,
        "humanReviewStatus": "pending",
    }
    record["environment"] = {
        "platformFamily": platform_family,
        "operatingSystem": {"name": os_name.strip(), "version": os_version.strip()},
        "browser": (
            {"name": browser_name.strip(), "version": browser_version.strip()}
            if browser_name and browser_version
            else None
        ),
        "physicalDevice": bool(physical_device),
        "assistiveTechnologies": [],
        "evidenceReferences": [],
    }
    record["supportClaims"] = {
        "screenReaderClaimed": bool(screen_reader_claimed),
        "voiceControlClaimed": bool(voice_control_claimed),
        "switchControlClaimed": bool(switch_control_claimed),
    }

    conditional = load_json(PLAN).get("claimConditionalScenarios", {})
    claims = record["supportClaims"]
    scenario_map = {item["id"]: item for item in record["scenarioResults"]}
    for claim_key, scenario_id in conditional.items():
        entry = scenario_map[scenario_id]
        if claims.get(claim_key) is True:
            entry["result"] = "not-tested"
            entry["notes"] = "PENDING real evidence because the prepared packet declares this support claim."
        else:
            entry["result"] = "not-applicable"
            entry["notes"] = "Not required unless the corresponding support claim is asserted."
        entry["evidenceReferences"] = []

    record["issues"] = [{
        "summary": "Prepared qualification packet only; real accessibility observations and authorized review acceptance have not yet been captured.",
        "severity": "info",
        "resolved": False,
        "reference": "contracts/v1.4/accessibility-qualification.candidate.json",
    }]
    record["disposition"] = {
        "evaluatorDisposition": "blocked",
        "acceptedForAccessibilityQualification": False,
        "acceptedForLifecycleGate": False,
        "notes": "PREPARED PACKET ONLY. No qualification, consumer conformance, or lifecycle promotion is granted.",
    }
    assert_prepared_fail_closed(record)
    return record


def assert_prepared_fail_closed(record: dict[str, Any]) -> None:
    req(record.get("status") == "in-progress", "prepared record must initialize in-progress")
    review = record.get("reviewAuthority", {})
    req(review.get("humanReviewStatus") == "pending", "prepared record must initialize human review pending")
    disposition = record.get("disposition", {})
    req(disposition.get("evaluatorDisposition") == "blocked", "prepared record must initialize blocked")
    req(disposition.get("acceptedForAccessibilityQualification") is False, "prepared record must not grant accessibility qualification")
    req(disposition.get("acceptedForLifecycleGate") is False, "prepared record must not grant lifecycle acceptance")
    target = record.get("target", {})
    validate_revision(str(target.get("sourceRevision", "")), "source revision")
    validate_revision(str(target.get("sourceTreeRevision", "")), "source tree revision")

    environment = record.get("environment", {})
    req(environment.get("evidenceReferences") == [], "prepared environment must not fabricate evidence references")
    for observation in record.get("preferenceCoverage", {}).values():
        req(observation.get("state") == "not-tested", "prepared preference coverage must remain not-tested")
        req(observation.get("evidenceReferences") == [], "prepared preference coverage must not fabricate evidence")
    for scenario in record.get("scenarioResults", []):
        req(scenario.get("result") in {"not-tested", "not-applicable"}, "prepared scenarios may not claim pass/fail results")
        req(scenario.get("evidenceReferences") == [], "prepared scenarios must not fabricate evidence references")

    evaluator = _load_evaluator()
    result = evaluator.evaluate_record(record, load_json(PLAN))
    req(result.get("evaluatorDisposition") == "blocked", "prepared record must deterministically evaluate as blocked")
    req(result.get("acceptedForAccessibilityQualification") is False, "evaluator must reject prepared record acceptance")
    req(result.get("acceptedForLifecycleGate") is False, "evaluator must keep lifecycle-gate acceptance false")


def build_checklist(record: dict[str, Any]) -> str:
    plan = load_json(PLAN)
    target = record["target"]
    claims = record["supportClaims"]
    required = list(plan["requiredScenarios"])
    for claim_key, scenario_id in plan["claimConditionalScenarios"].items():
        if claims.get(claim_key) is True:
            required.append(scenario_id)

    lines = [
        "# Glaze UI V1.4 Accessibility Qualification Capture Checklist",
        "",
        "> Prepared evidence packet only. Completing this checklist does not itself grant qualification or lifecycle status.",
        "",
        f"- Source revision: `{target['sourceRevision']}`",
        f"- Source tree revision: `{target['sourceTreeRevision']}`",
        f"- Review mode: `{record['reviewAuthority']['mode']}`",
        f"- Review authority: {record['reviewAuthority']['authority']}",
        "",
        "## Before testing",
        "",
        "- Verify the checked-out/runtime source exactly matches both immutable revisions above.",
        "- Record the real browser/OS/device environment and any assistive technologies actually used.",
        "- Keep evidence local and purpose-limited; do not add telemetry, analytics, screen capture, or remote collection solely for this packet.",
        "- Do not convert browser feature detection or automated regressions into qualification evidence.",
        "",
        "## Required preference evidence",
        "",
    ]
    for preference in plan["preferenceEvidence"]["requiredPreferences"]:
        lines.append(f"- [ ] `{preference}` — record tested-active/tested-inactive or evidenced not-supported with immutable evidence references.")
    lines.extend(["", "## Required scenarios", ""])
    for scenario_id in required:
        lines.append(f"- [ ] `{scenario_id}` — record the real result, evidence references, and concise notes.")
    lines.extend([
        "",
        "## Review and disposition",
        "",
        "- [ ] Resolve or explicitly retain every issue; unresolved high/critical issues block acceptance.",
        "- [ ] Human review status remains pending until an authorized reviewer actually accepts or rejects the captured evidence.",
        "- [ ] Run the deterministic evaluator against the completed record and exact expected source/tree revisions.",
        "- [ ] Preserve `acceptedForLifecycleGate: false`; accessibility-slice acceptance cannot promote V1.4 or grant consumer conformance.",
        "",
    ])
    return "\n".join(lines)


def resolve_output_dir(path: Path) -> Path:
    output = path.expanduser()
    output = (ROOT / output).resolve() if not output.is_absolute() else output.resolve()
    try:
        output.relative_to(DRAFT_ROOT)
    except ValueError as exc:
        raise PreparationError(
            f"packet output must stay under {DRAFT_ROOT.relative_to(ROOT)}; accepted evidence belongs under evidence/v1.4 only after real governed review"
        ) from exc
    req(output != DRAFT_ROOT, "packet output must be a named child directory, not the draft root itself")
    return output


def write_packet(output_dir: Path, record: dict[str, Any], checklist: str, *, force: bool = False) -> None:
    output_dir = resolve_output_dir(output_dir)
    req(force or not output_dir.exists(), f"refusing to overwrite existing qualification packet: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "qualification-record.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "CAPTURE-CHECKLIST.md").write_text(checklist, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--authority", required=True)
    parser.add_argument("--review-mode", choices=["human", "combined", "automated"], default="human")
    parser.add_argument("--source-revision", help="Exact source commit; defaults to checked-out Git HEAD")
    parser.add_argument("--source-tree-revision", help="Exact source tree; defaults to the selected source commit tree")
    parser.add_argument("--platform-family", choices=["web", "android", "linux", "other"], required=True)
    parser.add_argument("--os-name", required=True)
    parser.add_argument("--os-version", required=True)
    parser.add_argument("--browser-name")
    parser.add_argument("--browser-version")
    parser.add_argument("--physical-device", action="store_true")
    parser.add_argument("--claim-screen-reader", action="store_true")
    parser.add_argument("--claim-voice-control", action="store_true")
    parser.add_argument("--claim-switch-control", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    source_revision = validate_revision(args.source_revision, "source revision") if args.source_revision else git_revision()
    source_tree_revision = (
        validate_revision(args.source_tree_revision, "source tree revision")
        if args.source_tree_revision
        else git_tree_revision(source_revision)
    )
    record = build_record(
        authority=args.authority,
        review_mode=args.review_mode,
        source_revision=source_revision,
        source_tree_revision=source_tree_revision,
        platform_family=args.platform_family,
        os_name=args.os_name,
        os_version=args.os_version,
        browser_name=args.browser_name,
        browser_version=args.browser_version,
        physical_device=args.physical_device,
        screen_reader_claimed=args.claim_screen_reader,
        voice_control_claimed=args.claim_voice_control,
        switch_control_claimed=args.claim_switch_control,
    )
    output = resolve_output_dir(args.output_dir)
    write_packet(output, record, build_checklist(record), force=args.force)
    print(f"Created fail-closed V1.4 accessibility qualification packet: {output.relative_to(ROOT)}")
    print(f"Exact source revision: {source_revision}")
    print(f"Exact source tree revision: {source_tree_revision}")
    print("Status: in-progress; evaluatorDisposition: blocked")
    print("acceptedForAccessibilityQualification: false; acceptedForLifecycleGate: false")
    print("This packet is a preparation aid only and contains no fabricated qualification evidence.")


if __name__ == "__main__":
    try:
        main()
    except PreparationError as exc:
        raise SystemExit(f"Glaze UI V1.4 accessibility qualification packet preparation failed: {exc}")

#!/usr/bin/env python3
"""Generate and validate an exact-head Glaze UI V1.2 Candidate source inventory.

This is source-integrity/provenance evidence only. Inventory membership does not
establish conformance, human acceptance, runtime acceptance, Release Candidate
status, Stable status, or downstream consumer eligibility.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "contracts" / "v1.2" / "source-inventory.candidate.json"
EXPECTED_VERSION = "1.2.0-candidate"
EXPECTED_STABLE = "1.1.0"
EXPECTED_REPOSITORY = "GoreeCloud/goreecloud-glaze-ui"


def fail(message: str) -> None:
    raise SystemExit(f"Glaze V1.2 source-inventory validation failed: {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def git(*args: str, text: bool = True) -> str | bytes:
    try:
        return subprocess.check_output(
            ["git", "-C", str(ROOT), *args],
            text=text,
            stderr=subprocess.STDOUT,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "output", None)
        fail(f"git {' '.join(args)} failed" + (f": {str(detail).strip()}" if detail else ""))
        raise AssertionError("unreachable") from exc


def load_json(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing JSON source: {path.relative_to(ROOT)}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"invalid JSON source {path.relative_to(ROOT)}: {exc}")
    require(isinstance(value, dict), f"JSON source must be an object: {path.relative_to(ROOT)}")
    return value


def tracked_paths() -> list[str]:
    raw = git("ls-files", "-z", text=False)
    assert isinstance(raw, bytes)
    try:
        values = [part.decode("utf-8") for part in raw.split(b"\0") if part]
    except UnicodeDecodeError as exc:
        fail(f"tracked path is not valid UTF-8: {exc}")
    require(values, "repository has no Git-tracked files")
    return values


def selector_matches(path: str, selector: dict[str, Any]) -> bool:
    prefix = selector.get("prefix")
    suffix = selector.get("suffix")
    contains = selector.get("contains")
    if prefix is not None and not path.startswith(prefix):
        return False
    if suffix is not None and not path.endswith(suffix):
        return False
    if contains is not None and contains not in path:
        return False
    return True


def validate_contract(contract: dict[str, Any]) -> None:
    require(contract.get("schemaVersion") == 1, "unexpected source-inventory schemaVersion")
    require(contract.get("version") == EXPECTED_VERSION, "source-inventory version drifted")
    require(contract.get("lifecycle") == "candidate", "source inventory must remain Candidate")
    require(contract.get("consumerEligible") is False, "source inventory cannot be consumer eligible")
    require(contract.get("stableBaseline") == EXPECTED_STABLE, "Stable baseline drifted")
    require(contract.get("repository") == EXPECTED_REPOSITORY, "repository authority drifted")

    selectors = contract.get("selectors")
    require(isinstance(selectors, list) and selectors, "selectors must be a non-empty array")
    ids: set[str] = set()
    for selector in selectors:
        require(isinstance(selector, dict), "each selector must be an object")
        selector_id = selector.get("id")
        require(isinstance(selector_id, str) and selector_id.strip(), "selector id is required")
        require(selector_id not in ids, f"duplicate selector id: {selector_id}")
        ids.add(selector_id)
        require(
            any(isinstance(selector.get(key), str) and selector.get(key) for key in ("prefix", "suffix", "contains")),
            f"selector {selector_id} has no path constraint",
        )
        min_count = selector.get("minCount")
        require(isinstance(min_count, int) and not isinstance(min_count, bool) and min_count >= 1, f"selector {selector_id} has invalid minCount")

    anchors = contract.get("requiredAnchors")
    require(isinstance(anchors, list) and anchors, "requiredAnchors must be non-empty")
    require(all(isinstance(value, str) and value for value in anchors), "requiredAnchors contains an invalid path")
    require(len(anchors) == len(set(anchors)), "requiredAnchors contains duplicates")

    integrity = contract.get("integrity") or {}
    require(integrity.get("gitTrackedOnly") is True, "Git-tracked-only integrity must remain enabled")
    require(integrity.get("exactHeadRequired") is True, "exact-head integrity must remain enabled")
    require(integrity.get("caseFoldUniquePaths") is True, "case-fold path uniqueness must remain enabled")
    require(integrity.get("parseSelectedJson") is True, "selected JSON parsing must remain enabled")
    require(
        integrity.get("inventoryFields") == ["path", "categories", "bytes", "gitBlobSha1", "sha256"],
        "inventory evidence fields drifted",
    )

    authority = contract.get("authority") or {}
    require(authority.get("currentStable") == EXPECTED_STABLE, "contract currentStable drifted")
    require(authority.get("currentOfficial") == EXPECTED_STABLE, "contract currentOfficial drifted")
    require(authority.get("activeCandidate") == EXPECTED_VERSION, "contract activeCandidate drifted")
    for field in (
        "inventoryImpliesAcceptance",
        "inventoryImpliesReleaseCandidate",
        "inventoryImpliesStable",
        "inventoryImpliesConsumerConformance",
        "inventoryImpliesHumanAcceptance",
        "inventoryImpliesRuntimeAcceptance",
    ):
        require(authority.get(field) is False, f"source inventory must not imply {field}")


def validate_lifecycle() -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    require(version == EXPECTED_STABLE, f"VERSION must remain {EXPECTED_STABLE}, found {version!r}")

    lifecycle = load_json(ROOT / "registry" / "lifecycle.json")
    require(lifecycle.get("currentOfficial") == EXPECTED_STABLE, "currentOfficial must remain V1.1 Stable")
    require(lifecycle.get("currentStable") == EXPECTED_STABLE, "currentStable must remain V1.1 Stable")
    require(lifecycle.get("activeCandidate") == EXPECTED_VERSION, "activeCandidate must remain V1.2 Candidate")
    releases = lifecycle.get("releases") or []
    candidate = next((item for item in releases if isinstance(item, dict) and item.get("version") == EXPECTED_VERSION), None)
    require(candidate is not None, "lifecycle registry is missing V1.2 Candidate release entry")
    require(candidate.get("status") == "candidate", "V1.2 lifecycle release entry is not Candidate")
    require(candidate.get("consumerEligible") is False, "V1.2 lifecycle release entry became consumer eligible")
    require(candidate.get("stableBaseline") == EXPECTED_STABLE, "V1.2 lifecycle Stable baseline drifted")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/glaze-v1.2-source-inventory.json")
    args = parser.parse_args()

    contract = load_json(CONTRACT_PATH)
    validate_contract(contract)
    validate_lifecycle()

    head = str(git("rev-parse", "HEAD")).strip()
    require(len(head) == 40 and all(c in "0123456789abcdef" for c in head), "HEAD is not an exact lowercase 40-character Git revision")
    tracked = tracked_paths()
    tracked_set = set(tracked)

    tracked_changes = str(git("status", "--porcelain", "--untracked-files=no")).strip()
    require(not tracked_changes, f"tracked worktree differs from exact HEAD: {tracked_changes}")

    categories: dict[str, set[str]] = {}
    for selector in contract["selectors"]:
        selector_id = selector["id"]
        matches = {path for path in tracked if selector_matches(path, selector)}
        require(len(matches) >= selector["minCount"], f"selector {selector_id} matched only {len(matches)} files")
        for path in matches:
            categories.setdefault(path, set()).add(selector_id)

    for anchor in contract["requiredAnchors"]:
        require(anchor in tracked_set, f"required anchor is not Git tracked: {anchor}")
        require((ROOT / anchor).is_file(), f"required anchor is not a file: {anchor}")
        categories.setdefault(anchor, set()).add("required-anchor")

    inventory_paths = sorted(categories)
    require(inventory_paths, "source inventory selection is empty")

    folded: dict[str, str] = {}
    for path in inventory_paths:
        key = path.casefold()
        previous = folded.get(key)
        require(previous is None or previous == path, f"case-fold path collision: {previous!r} and {path!r}")
        folded[key] = path

    if (contract.get("integrity") or {}).get("parseSelectedJson") is True:
        for path in inventory_paths:
            if path.endswith(".json"):
                load_json(ROOT / path)

    entries: list[dict[str, Any]] = []
    for path in inventory_paths:
        file_path = ROOT / path
        require(file_path.is_file(), f"selected tracked path is not a regular file: {path}")
        raw = file_path.read_bytes()
        blob_sha = str(git("hash-object", "--no-filters", "--", path)).strip()
        require(len(blob_sha) == 40 and all(c in "0123456789abcdef" for c in blob_sha), f"invalid Git blob SHA for {path}")
        entries.append(
            {
                "path": path,
                "categories": sorted(categories[path]),
                "bytes": len(raw),
                "gitBlobSha1": blob_sha,
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )

    commit_time = str(git("show", "-s", "--format=%cI", "HEAD")).strip()
    report = {
        "schemaVersion": 1,
        "kind": "glaze-v1.2-candidate-source-inventory",
        "repository": EXPECTED_REPOSITORY,
        "head": head,
        "commitTime": commit_time,
        "version": EXPECTED_VERSION,
        "lifecycle": "candidate",
        "stableBaseline": EXPECTED_STABLE,
        "consumerEligible": False,
        "acceptanceImplied": False,
        "releaseCandidateImplied": False,
        "stableImplied": False,
        "humanAcceptanceImplied": False,
        "runtimeAcceptanceImplied": False,
        "entryCount": len(entries),
        "entries": entries,
    }

    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        f"Glaze V1.2 Candidate source inventory validated: {len(entries)} tracked sources at {head}. "
        "Source integrity only; no RC, Stable, human, runtime, or consumer acceptance implied."
    )


if __name__ == "__main__":
    main()

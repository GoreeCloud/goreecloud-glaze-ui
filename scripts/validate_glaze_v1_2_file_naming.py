#!/usr/bin/env python3
"""Validate canonical naming for the ordinary Glaze UI V1.2 Candidate surface.

This validator intentionally does not normalize nested native/framework paths.
Repository/framework conventions remain authoritative there. A green result is
naming/source-integrity evidence only and never lifecycle or acceptance evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "v1.2" / "file-naming.candidate.json"
EXPECTED_VERSION = "1.2.0-candidate"
EXPECTED_STABLE = "1.1.0"
EXPECTED_REPOSITORY = "GoreeCloud/goreecloud-glaze-ui"


def fail(message: str) -> None:
    raise SystemExit(f"Glaze V1.2 file-naming validation failed: {message}")


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
        result = [item.decode("utf-8") for item in raw.split(b"\0") if item]
    except UnicodeDecodeError as exc:
        fail(f"tracked path is not valid UTF-8: {exc}")
    require(result, "repository has no Git-tracked paths")
    return result


def validate_contract(contract: dict[str, Any]) -> None:
    require(contract.get("schemaVersion") == 1, "unexpected naming schemaVersion")
    require(contract.get("version") == EXPECTED_VERSION, "naming contract version drifted")
    require(contract.get("lifecycle") == "candidate", "naming contract must remain Candidate")
    require(contract.get("consumerEligible") is False, "naming contract cannot be consumer eligible")
    require(contract.get("stableBaseline") == EXPECTED_STABLE, "Stable baseline drifted")
    require(contract.get("repository") == EXPECTED_REPOSITORY, "repository authority drifted")

    tokens = contract.get("temporaryTokens")
    require(tokens == ["old", "copy", "temp", "latest", "final", "backup", "new"], "temporary-token policy drifted")

    namespaces = contract.get("ordinaryNamespaces")
    require(isinstance(namespaces, dict) and namespaces, "ordinaryNamespaces must be a non-empty object")
    for name, rule in namespaces.items():
        require(isinstance(rule, dict), f"namespace {name} must be an object")
        require(isinstance(rule.get("prefix"), str) and rule["prefix"], f"namespace {name} requires prefix")
        require(isinstance(rule.get("pattern"), str) and rule["pattern"], f"namespace {name} requires pattern")
        try:
            re.compile(rule["pattern"])
        except re.error as exc:
            fail(f"namespace {name} has invalid pattern: {exc}")

    exceptions = contract.get("explicitPathExceptions")
    require(isinstance(exceptions, dict) and exceptions, "explicitPathExceptions must be a non-empty object")
    for path, reason in exceptions.items():
        require(isinstance(path, str) and path, "exception path is invalid")
        require(isinstance(reason, str) and reason.strip(), f"exception {path} requires a reason")

    framework = contract.get("frameworkBoundaries") or {}
    require(framework.get("nestedReferencePaths") == "report-but-do-not-normalize", "nested reference boundary drifted")
    require(framework.get("nativeFrameworkPaths") == "repository-or-framework-convention-wins", "native/framework boundary drifted")

    integrity = contract.get("integrity") or {}
    for field in (
        "gitTrackedOnly",
        "exactHeadRequired",
        "caseFoldUniqueControlledPaths",
        "spacesProhibitedInOrdinaryControlledPaths",
        "temporaryTokensProhibitedAsCompleteNameTokens",
        "automaticRenamesProhibited",
    ):
        require(integrity.get(field) is True, f"naming integrity rule weakened: {field}")

    authority = contract.get("authority") or {}
    require(authority.get("currentStable") == EXPECTED_STABLE, "currentStable drifted")
    require(authority.get("currentOfficial") == EXPECTED_STABLE, "currentOfficial drifted")
    require(authority.get("activeCandidate") == EXPECTED_VERSION, "activeCandidate drifted")
    for field in (
        "namingValidationImpliesSourceApproval",
        "namingValidationImpliesReleaseCandidate",
        "namingValidationImpliesStable",
        "namingValidationImpliesConsumerConformance",
        "namingValidationImpliesRuntimeAcceptance",
        "namingValidationImpliesHumanAcceptance",
    ):
        require(authority.get(field) is False, f"naming validation must not imply {field}")


def validate_lifecycle() -> None:
    require((ROOT / "VERSION").read_text(encoding="utf-8").strip() == EXPECTED_STABLE, "VERSION moved away from Stable 1.1.0")
    lifecycle = load_json(ROOT / "registry" / "lifecycle.json")
    require(lifecycle.get("currentStable") == EXPECTED_STABLE, "lifecycle currentStable drifted")
    require(lifecycle.get("currentOfficial") == EXPECTED_STABLE, "lifecycle currentOfficial drifted")
    require(lifecycle.get("activeCandidate") == EXPECTED_VERSION, "lifecycle activeCandidate drifted")
    candidate = next(
        (item for item in lifecycle.get("releases", []) if isinstance(item, dict) and item.get("version") == EXPECTED_VERSION),
        None,
    )
    require(candidate is not None, "V1.2 Candidate lifecycle entry is missing")
    require(candidate.get("status") == "candidate", "V1.2 lifecycle status drifted")
    require(candidate.get("consumerEligible") is False, "V1.2 became consumer eligible")
    require(candidate.get("stableBaseline") == EXPECTED_STABLE, "V1.2 Stable baseline drifted")


def is_immediate_reference(path: str) -> bool:
    prefix = "reference/v1.2/"
    if not path.startswith(prefix):
        return False
    remainder = path[len(prefix):]
    return bool(remainder) and "/" not in remainder


def select_paths(paths: list[str], rule: dict[str, Any]) -> list[str]:
    prefix = rule["prefix"]
    result = [path for path in paths if path.startswith(prefix)]
    contains = rule.get("contains")
    if isinstance(contains, str) and contains:
        result = [path for path in result if contains in path]
    if rule.get("immediateFilesOnly") is True:
        result = [path for path in result if is_immediate_reference(path)]
    return sorted(result)


def complete_tokens(path: str) -> set[str]:
    # Temporary naming words are prohibited only as complete filename/path tokens,
    # avoiding false positives such as "renewal" containing "new".
    return {token.casefold() for token in re.split(r"[/._-]+", path) if token}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/glaze-v1.2-file-naming.json")
    args = parser.parse_args()

    contract = load_json(CONTRACT)
    validate_contract(contract)
    validate_lifecycle()

    head = str(git("rev-parse", "HEAD")).strip()
    require(re.fullmatch(r"[0-9a-f]{40}", head) is not None, "HEAD is not an exact lowercase Git revision")
    require(not str(git("status", "--porcelain", "--untracked-files=no")).strip(), "tracked worktree differs from exact HEAD")

    tracked = tracked_paths()
    tracked_set = set(tracked)
    exceptions: dict[str, str] = contract["explicitPathExceptions"]
    for path in exceptions:
        require(path in tracked_set, f"documented naming exception is not Git tracked: {path}")

    namespaces: dict[str, dict[str, Any]] = contract["ordinaryNamespaces"]
    controlled: dict[str, set[str]] = {}
    namespace_counts: dict[str, int] = {}
    for namespace, rule in namespaces.items():
        selected = select_paths(tracked, rule)
        require(selected, f"namespace {namespace} selected no tracked paths")
        namespace_counts[namespace] = len(selected)
        pattern = re.compile(rule["pattern"])
        for path in selected:
            controlled.setdefault(path, set()).add(namespace)
            if path in exceptions:
                continue
            require(pattern.fullmatch(path) is not None, f"non-canonical {namespace} path: {path}")
            require(" " not in path, f"space is prohibited in ordinary controlled path: {path}")

    # Explicit non-namespace controls are still part of the collision/token audit.
    for path in exceptions:
        controlled.setdefault(path, set()).add("explicit-exception")

    bad_tokens = set(contract["temporaryTokens"])
    for path in controlled:
        prohibited = sorted(complete_tokens(path) & bad_tokens)
        require(not prohibited, f"temporary naming token(s) {prohibited} in controlled path: {path}")

    folded: dict[str, str] = {}
    for path in sorted(controlled):
        key = path.casefold()
        previous = folded.get(key)
        require(previous is None or previous == path, f"case-fold naming collision: {previous!r} and {path!r}")
        folded[key] = path

    # Nested V1.2 reference/native paths are intentionally visible in evidence but
    # excluded from cosmetic normalization because repository/framework conventions win.
    nested_reference_paths = sorted(
        path for path in tracked
        if path.startswith("reference/v1.2/") and not is_immediate_reference(path)
    )
    nested_roots = sorted({PurePosixPath(path).parts[2] for path in nested_reference_paths if len(PurePosixPath(path).parts) > 2})

    report = {
        "schemaVersion": 1,
        "kind": "glaze-v1.2-candidate-file-naming",
        "repository": EXPECTED_REPOSITORY,
        "head": head,
        "version": EXPECTED_VERSION,
        "lifecycle": "candidate",
        "stableBaseline": EXPECTED_STABLE,
        "consumerEligible": False,
        "controlledPathCount": len(controlled),
        "namespaceCounts": namespace_counts,
        "controlledPaths": [
            {"path": path, "classifications": sorted(controlled[path]), "exceptionReason": exceptions.get(path)}
            for path in sorted(controlled)
        ],
        "nestedReferencePathCount": len(nested_reference_paths),
        "nestedReferenceRoots": nested_roots,
        "nestedReferencePathsNormalized": False,
        "automaticRenamesPerformed": False,
        "sourceApprovalImplied": False,
        "releaseCandidateImplied": False,
        "stableImplied": False,
        "consumerConformanceImplied": False,
        "runtimeAcceptanceImplied": False,
        "humanAcceptanceImplied": False,
    }

    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        f"Glaze V1.2 Candidate canonical naming validated for {len(controlled)} controlled paths at {head}; "
        f"{len(nested_reference_paths)} nested reference/native paths reported without normalization. "
        "Naming evidence only; no RC, Stable, runtime, human, or consumer acceptance implied."
    )


if __name__ == "__main__":
    main()

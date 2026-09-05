#!/usr/bin/env python3
"""Fail-closed semantic namespace validation for Glaze UI V1.2 Candidate contracts."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DIR = ROOT / "contracts" / "v1.2"
CONTROL = CONTRACT_DIR / "contract-namespace.candidate.json"
VERSION = ROOT / "VERSION"
LIFECYCLE = ROOT / "registry" / "lifecycle.json"
CANDIDATE_SUFFIX = ".candidate.json"
CANDIDATE_VERSION = "1.2.0-candidate"
STABLE_VERSION = "1.1.0"
JSON_SCHEMA_2020_12 = "https://json-schema.org/draft/2020-12/schema"
PATH_RE = re.compile(r"^contracts/v1\.2/[A-Za-z0-9._/-]+\.json$")
FILENAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.candidate\.json$")
HEAD_RE = re.compile(r"^[0-9a-f]{40}$")


class NamespaceError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise NamespaceError(message)


def load_json(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected JSON object in {path.relative_to(ROOT)}")
    return value


def head_revision() -> str:
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    require(HEAD_RE.fullmatch(revision) is not None, f"invalid Git HEAD: {revision!r}")
    return revision


def tracked_paths() -> set[str]:
    raw = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
    return {item.decode("utf-8") for item in raw.split(b"\0") if item}


def require_clean_tracked_worktree() -> None:
    require(subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], cwd=ROOT).returncode == 0,
            "tracked worktree differs from HEAD")
    require(subprocess.run(["git", "diff", "--cached", "--quiet", "HEAD", "--"], cwd=ROOT).returncode == 0,
            "index differs from HEAD")


def iter_strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from iter_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_strings(child)


def normalized(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def stable_baseline_version(value: Any, path: str) -> str:
    if isinstance(value, str):
        require(value == STABLE_VERSION, f"{path}: stableBaseline drifted from {STABLE_VERSION}")
        return value
    require(isinstance(value, dict), f"{path}: stableBaseline must be string or object")
    require(value.get("version") == STABLE_VERSION,
            f"{path}: nested stableBaseline.version drifted from {STABLE_VERSION}")
    if "consumerEligible" in value:
        require(value.get("consumerEligible") is True,
                f"{path}: Stable baseline consumerEligible must remain true")
    return STABLE_VERSION


def validate_control(control: dict[str, Any]) -> None:
    require(control.get("schemaVersion") == 1, "namespace-control schemaVersion drifted")
    require(control.get("id") == "goreecloud.glaze-ui.v1.2.contract-namespace.candidate",
            "namespace-control id drifted")
    require(control.get("version") == CANDIDATE_VERSION, "namespace-control Candidate version drifted")
    require(control.get("lifecycle") == "candidate", "namespace-control lifecycle drifted")
    require(control.get("consumerEligible") is False, "namespace-control became consumer eligible")
    require(control.get("stableBaseline") == STABLE_VERSION, "namespace-control Stable baseline drifted")
    scope = control.get("scope", {})
    require(scope.get("directory") == "contracts/v1.2" and scope.get("candidateSuffix") == CANDIDATE_SUFFIX
            and scope.get("immediateFilesOnly") is True, "namespace-control scope drifted")
    rules = control.get("rules", {})
    for key in (
        "candidateFilenameNamespaceUnique", "contractIdsUniqueWhenPresent",
        "contractIdMustContainFilenameNamespaceWhenPresent",
        "contractIdMustRemainCandidateScopedWhenPresent", "schemaVersionOneWhenPresent",
        "jsonSchema202012WhenDeclared", "lifecycleMustRemainCandidateScopedWhenPresent",
        "topLevelCandidateVersionMustRemainCandidateWhenPresent",
        "topLevelConsumerEligibilityMustRemainFalseWhenPresent",
        "stableBaselineMustResolveTo110WhenPresent",
        "nestedMigrationTargetMustRemainCandidateAndNonConsumerEligibleWhenPresent",
        "intraV12CandidateContractReferencesMustResolve", "intraV12JsonReferencesMustUseCandidateSuffix",
        "trackedWorktreeMustMatchHead", "stableAuthorityMayNotMove", "validatorMayNotRewriteContracts",
    ):
        require(rules.get(key) is True, f"namespace-control rule drifted: {key}")


def lifecycle_release(lifecycle: dict[str, Any], version: str) -> dict[str, Any]:
    matches = [item for item in lifecycle.get("releases", [])
               if isinstance(item, dict) and item.get("version") == version]
    require(len(matches) == 1, f"lifecycle release entry missing/ambiguous for {version}")
    return matches[0]


def validate_repository_authority() -> None:
    require(VERSION.read_text(encoding="utf-8").strip() == STABLE_VERSION,
            "VERSION moved away from Stable 1.1.0")
    lifecycle = load_json(LIFECYCLE)
    require(lifecycle.get("currentStable") == STABLE_VERSION and lifecycle.get("currentOfficial") == STABLE_VERSION,
            "Stable/current official lifecycle authority moved")
    require(lifecycle.get("activeCandidate") == CANDIDATE_VERSION,
            "active Candidate lifecycle identity drifted")
    stable = lifecycle_release(lifecycle, STABLE_VERSION)
    candidate = lifecycle_release(lifecycle, CANDIDATE_VERSION)
    require(stable.get("status") == "stable" and stable.get("consumerEligible") is True,
            "Stable release authority drifted")
    require(candidate.get("status") == "candidate" and candidate.get("consumerEligible") is False,
            "Candidate release authority drifted")


def candidate_files(tracked: set[str]) -> list[Path]:
    prefix = "contracts/v1.2/"
    names = sorted(path for path in tracked
                   if path.startswith(prefix)
                   and "/" not in path[len(prefix):]
                   and path.endswith(CANDIDATE_SUFFIX))
    require(names, "no immediate V1.2 Candidate contracts found")
    for relative in names:
        require(FILENAME_RE.fullmatch(Path(relative).name) is not None,
                f"non-canonical Candidate contract filename: {relative}")
    require(len({Path(path).name.removesuffix(CANDIDATE_SUFFIX).casefold() for path in names}) == len(names),
            "Candidate contract filename namespace collision detected")
    return [ROOT / path for path in names]


def validate_one(path: Path, data: dict[str, Any], tracked: set[str], seen_ids: dict[str, str]) -> dict[str, Any]:
    relative = path.relative_to(ROOT).as_posix()
    namespace = path.name.removesuffix(CANDIDATE_SUFFIX)

    if "schemaVersion" in data:
        require(data.get("schemaVersion") == 1, f"{relative}: schemaVersion must remain 1")
    if "$schema" in data:
        require(data.get("$schema") == JSON_SCHEMA_2020_12,
                f"{relative}: declared JSON Schema authority is not Draft 2020-12")
    if "version" in data:
        require(data.get("version") == CANDIDATE_VERSION,
                f"{relative}: top-level version is not {CANDIDATE_VERSION}")
    if "lifecycle" in data:
        lifecycle = data.get("lifecycle")
        require(isinstance(lifecycle, str) and lifecycle.startswith("candidate"),
                f"{relative}: lifecycle is not Candidate-scoped")
    if "consumerEligible" in data:
        require(data.get("consumerEligible") is False,
                f"{relative}: Candidate contract became consumer eligible")
    if "stableBaseline" in data:
        stable_baseline_version(data.get("stableBaseline"), relative)

    target = data.get("target")
    if isinstance(target, dict) and "version" in target:
        require(target.get("version") == CANDIDATE_VERSION,
                f"{relative}: nested target.version is not {CANDIDATE_VERSION}")
        if "consumerEligible" in target:
            require(target.get("consumerEligible") is False,
                    f"{relative}: nested Candidate target became consumer eligible")

    contract_id = data.get("id")
    if contract_id is not None:
        require(isinstance(contract_id, str) and contract_id.strip(), f"{relative}: id must be a non-empty string")
        prefixes = ("goreecloud.glaze-ui.v1.2.", "glaze-v1.")
        require(contract_id.startswith(prefixes), f"{relative}: contract id uses an unexpected namespace prefix")
        require("candidate" in contract_id.lower(), f"{relative}: contract id is not Candidate-scoped")
        require(normalized(namespace) in normalized(contract_id),
                f"{relative}: contract id does not contain filename namespace {namespace!r}")
        folded = contract_id.casefold()
        require(folded not in seen_ids, f"duplicate contract id in {relative} and {seen_ids.get(folded)}")
        seen_ids[folded] = relative

    references: list[str] = []
    for value in iter_strings(data):
        if not PATH_RE.fullmatch(value):
            continue
        references.append(value)
        require(value.endswith(CANDIDATE_SUFFIX),
                f"{relative}: intra-V1.2 JSON contract reference lacks Candidate suffix: {value}")
        require(value in tracked, f"{relative}: unresolved intra-V1.2 Candidate contract reference: {value}")

    return {
        "path": relative,
        "namespace": namespace,
        "id": contract_id,
        "lifecycle": data.get("lifecycle"),
        "version": data.get("version"),
        "consumerEligible": data.get("consumerEligible"),
        "referenceCount": len(references),
        "references": sorted(set(references)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/glaze-v1.2-contract-namespace.json")
    args = parser.parse_args()

    require_clean_tracked_worktree()
    revision = head_revision()
    tracked = tracked_paths()
    validate_repository_authority()
    control = load_json(CONTROL)
    validate_control(control)

    files = candidate_files(tracked)
    seen_ids: dict[str, str] = {}
    records = [validate_one(path, load_json(path), tracked, seen_ids) for path in files]

    report = {
        "schemaVersion": 1,
        "reportKind": "glaze-v1.2-candidate-contract-namespace-validation",
        "revision": revision,
        "repository": "GoreeCloud/goreecloud-glaze-ui",
        "stableBaseline": STABLE_VERSION,
        "candidateVersion": CANDIDATE_VERSION,
        "consumerEligible": False,
        "status": "bounded-namespace-consistent",
        "contractCount": len(records),
        "contractIdCount": len(seen_ids),
        "intraCandidateReferenceCount": sum(record["referenceCount"] for record in records),
        "contracts": records,
        "claims": {
            "contractContentApproved": False,
            "implementationAccepted": False,
            "runtimeAccepted": False,
            "nativeParityAccepted": False,
            "physicalDeviceAccepted": False,
            "humanAccepted": False,
            "releaseCandidateAccepted": False,
            "stableAccepted": False,
            "consumerConformanceAccepted": False,
        },
    }

    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    require_clean_tracked_worktree()
    print(f"Glaze V1.2 Candidate contract namespaces validated across {len(records)} contracts at {revision}; "
          f"{len(seen_ids)} IDs and {report['intraCandidateReferenceCount']} intra-Candidate references checked.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except NamespaceError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)

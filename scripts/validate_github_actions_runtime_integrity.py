#!/usr/bin/env python3
"""Validate GoreeCloud Glaze GitHub Actions runtime and immutable pin integrity.

This gate is repository-maintenance evidence only. It does not establish any Glaze
lifecycle, product, visual, accessibility, performance, native-platform, RC, Stable,
or consumer-conformance acceptance.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
OUT = ROOT / "artifacts" / "github-actions-runtime-integrity.json"

APPROVED_EXTERNAL_ACTIONS = {
    "actions/checkout": {
        "sha": "3d3c42e5aac5ba805825da76410c181273ba90b1",
        "release": "v7.0.1",
        "runtime": "node24-generation",
    },
    "actions/setup-python": {
        "sha": "5fda3b95a4ea91299a34e894583c3862153e4b97",
        "release": "v7.0.0",
        "runtime": "node24-generation",
    },
    "actions/setup-node": {
        "sha": "820762786026740c76f36085b0efc47a31fe5020",
        "release": "v7.0.0",
        "runtime": "node24-generation",
    },
    "actions/upload-artifact": {
        "sha": "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
        "release": "v7.0.1",
        "runtime": "node24-generation",
    },
}

# Workflow steps may spell an action either as an indented `uses:` key after a
# step name or in YAML's compact list-item form (`- uses:`). Both are security
# relevant and must be covered by the same immutable-pin policy.
USES = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", re.MULTILINE)
SHA = re.compile(r"^[0-9a-f]{40}$")
NODE20_OVERRIDE = "ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION"
LEGACY_NODE20_OVERRIDE = "FORCE_JAVASCRIPT_ACTIONS_TO_NODE20"


class IntegrityError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise IntegrityError(message)


def workflow_paths() -> list[Path]:
    paths = sorted([*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")])
    require(paths, "no GitHub Actions workflow files found")
    return paths


def parse_external(ref: str) -> tuple[str, str] | None:
    if ref.startswith("./"):
        return None
    require("@" in ref, f"external action reference has no immutable ref separator: {ref}")
    action, revision = ref.rsplit("@", 1)
    require(action in APPROVED_EXTERNAL_ACTIONS, f"unapproved external action family: {action}")
    require(SHA.fullmatch(revision) is not None, f"external action is not pinned to a 40-char lowercase SHA: {ref}")
    return action, revision


def validate() -> dict[str, object]:
    paths = workflow_paths()
    observed: dict[str, dict[str, object]] = {}
    local_reusable: set[str] = set()
    files_without_uses: list[str] = []

    for path in paths:
        text = path.read_text(encoding="utf-8")
        relative = str(path.relative_to(ROOT))
        require(NODE20_OVERRIDE not in text, f"deprecated/unsafe Node runtime override present in {relative}: {NODE20_OVERRIDE}")
        require(LEGACY_NODE20_OVERRIDE not in text, f"Node 20 opt-out override present in {relative}: {LEGACY_NODE20_OVERRIDE}")
        refs = USES.findall(text)
        if not refs:
            files_without_uses.append(relative)
            continue
        for ref in refs:
            try:
                parsed = parse_external(ref)
            except IntegrityError as error:
                raise IntegrityError(f"{relative}: {error}") from error
            if parsed is None:
                local_reusable.add(ref)
                continue
            action, revision = parsed
            expected = APPROVED_EXTERNAL_ACTIONS[action]
            require(
                revision == expected["sha"],
                f"{relative} pins {action} to {revision}, expected approved {expected['release']} SHA {expected['sha']}",
            )
            entry = observed.setdefault(action, {"count": 0, "workflows": []})
            entry["count"] = int(entry["count"]) + 1
            workflows = entry["workflows"]
            assert isinstance(workflows, list)
            workflows.append(relative)

    for action, expected in APPROVED_EXTERNAL_ACTIONS.items():
        require(action in observed, f"approved action family is not exercised by any workflow: {action}")
        observed[action]["approvedSha"] = expected["sha"]
        observed[action]["release"] = expected["release"]
        observed[action]["runtime"] = expected["runtime"]
        observed[action]["workflows"] = sorted(set(observed[action]["workflows"]))

    return {
        "schemaVersion": 1,
        "kind": "goreecloud-glaze-github-actions-runtime-integrity",
        "workflowCount": len(paths),
        "externalActionFamilies": observed,
        "localReusableWorkflows": sorted(local_reusable),
        "workflowFilesWithoutUses": files_without_uses,
        "immutableExternalPinsRequired": True,
        "node24GenerationRequired": True,
        "node20OverrideAllowed": False,
        "unapprovedExternalActionFamiliesAllowed": False,
        "lifecyclePromotionImplied": False,
        "releaseCandidateImplied": False,
        "stableImplied": False,
        "consumerConformanceImplied": False,
    }


def main() -> int:
    try:
        report = validate()
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(
            f"PASS: {report['workflowCount']} workflows use only approved immutable Node 24-generation action pins; "
            "no lifecycle or product acceptance is implied."
        )
        return 0
    except (IntegrityError, OSError) as error:
        print(f"FAIL: GitHub Actions runtime integrity: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

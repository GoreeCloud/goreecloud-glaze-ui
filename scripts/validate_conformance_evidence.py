#!/usr/bin/env python3
"""Validate GLAZE UI V1.2 conformance evidence without external dependencies."""

from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "VERSION"
CURRENT_PRODUCT_VERSION = "1.2.0"
FORM_FACTORS = {"mobile", "tablet", "desktop", "tv", "foldable", "wearable", "spatial"}
INTEGRATIONS = {
    "identity",
    "privacy_shield",
    "wardveil_security",
    "everkeep",
    "goreecloud_mesh",
}
TOP_LEVEL = {
    "schema_version",
    "producer",
    "target",
    "observed_at",
    "valid_until",
    "claim",
    "acceptance",
    "integral_platform_integrations",
    "evidence_references",
}
MAX_NAME_LENGTH = 160
MAX_REFERENCE_LENGTH = 500
MAX_EVIDENCE_REFERENCES = 50
MAX_INTEGRATION_REFERENCES = 20
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
RFC3339_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})$"
)


class EvidenceError(ValueError):
    """Evidence is structurally invalid or cannot support its stated claim."""


def require_object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceError(f"{name} must be an object")
    return value


def require_exact_keys(value: dict[str, Any], expected: set[str], name: str) -> None:
    keys = set(value)
    missing = sorted(expected - keys)
    unknown = sorted(keys - expected)
    if missing:
        raise EvidenceError(f"{name} is missing required field(s): {', '.join(missing)}")
    if unknown:
        raise EvidenceError(f"{name} contains unknown field(s): {', '.join(unknown)}")


def require_bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise EvidenceError(f"{name} must be boolean")
    return value


def require_bounded_string(value: Any, name: str, *, max_length: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > max_length:
        raise EvidenceError(
            f"{name} must be a bounded non-empty string of at most {max_length} characters"
        )
    return value


def require_references(
    value: Any,
    name: str,
    *,
    required: bool,
    max_items: int,
) -> list[str]:
    if not isinstance(value, list):
        raise EvidenceError(f"{name} must be an array")
    if required and not value:
        raise EvidenceError(f"{name} must contain at least one evidence reference")
    if len(value) > max_items:
        raise EvidenceError(f"{name} exceeds the {max_items}-item evidence-reference limit")
    normalized: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip() or len(item) > MAX_REFERENCE_LENGTH:
            raise EvidenceError(f"{name}[{index}] must be a bounded non-empty string")
        normalized.append(item.strip())
    if len(normalized) != len(set(normalized)):
        raise EvidenceError(f"{name} must not contain duplicate references")
    return normalized


def parse_datetime(value: Any, name: str) -> datetime:
    if not isinstance(value, str):
        raise EvidenceError(f"{name} must be an RFC 3339 date-time")
    text = value.strip()
    if not RFC3339_RE.fullmatch(text):
        raise EvidenceError(f"{name} must be an RFC 3339 date-time")
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise EvidenceError(f"{name} must be an RFC 3339 date-time") from exc
    if parsed.tzinfo is None:
        raise EvidenceError(f"{name} must include a timezone")
    return parsed.astimezone(UTC)


def validate_record(record: Any, *, now: datetime | None = None) -> dict[str, Any]:
    data = require_object(record, "evidence")
    require_exact_keys(data, TOP_LEVEL, "evidence")
    if data["schema_version"] != 2:
        raise EvidenceError("schema_version must be 2 for GLAZE UI V1.2 evidence")

    producer = require_object(data["producer"], "producer")
    require_exact_keys(producer, {"system", "authoritative"}, "producer")
    require_bounded_string(producer["system"], "producer.system", max_length=MAX_NAME_LENGTH)
    if producer["authoritative"] is not True:
        raise EvidenceError("evidence producer must be authoritative")

    target = require_object(data["target"], "target")
    require_exact_keys(
        target,
        {"application", "glaze_version", "source_revision", "form_factors"},
        "target",
    )
    require_bounded_string(
        target["application"], "target.application", max_length=MAX_NAME_LENGTH
    )
    repository_version = VERSION_FILE.read_text(encoding="utf-8").strip()
    if repository_version != CURRENT_PRODUCT_VERSION:
        raise EvidenceError(
            f"validator is bound to GLAZE UI V1.2 product version {CURRENT_PRODUCT_VERSION}, "
            f"repository reports {repository_version}"
        )
    if target["glaze_version"] != repository_version:
        raise EvidenceError(
            "target.glaze_version must match the current GLAZE UI V1.2 product version exactly"
        )
    if not isinstance(target["source_revision"], str) or not SHA_RE.fullmatch(
        target["source_revision"]
    ):
        raise EvidenceError("target.source_revision must be an exact lowercase 40-character SHA")
    factors = target["form_factors"]
    if not isinstance(factors, list) or not factors:
        raise EvidenceError("target.form_factors must be a non-empty array")
    if any(not isinstance(item, str) or item not in FORM_FACTORS for item in factors):
        raise EvidenceError("target.form_factors contains an unsupported GLAZE UI V1.2 role")
    if len(factors) != len(set(factors)):
        raise EvidenceError("target.form_factors must not contain duplicates")

    observed = parse_datetime(data["observed_at"], "observed_at")
    valid_until = parse_datetime(data["valid_until"], "valid_until")
    clock = now or datetime.now(UTC)
    if clock.tzinfo is None:
        raise EvidenceError("validation clock must include a timezone")
    clock = clock.astimezone(UTC)
    if observed > clock:
        raise EvidenceError("observed_at must not be in the future")
    if valid_until <= observed:
        raise EvidenceError("valid_until must be after observed_at")
    if valid_until <= clock:
        raise EvidenceError("evidence is expired")

    claim = require_object(data["claim"], "claim")
    require_exact_keys(claim, {"kind", "accepted"}, "claim")
    if claim["kind"] not in {"conformance", "production_ui_acceptance"}:
        raise EvidenceError("claim.kind is unsupported")
    accepted = require_bool(claim["accepted"], "claim.accepted")

    acceptance = require_object(data["acceptance"], "acceptance")
    require_exact_keys(
        acceptance,
        {"current_stable_required", "application_specific_acceptance_complete"},
        "acceptance",
    )
    if acceptance["current_stable_required"] is not True:
        raise EvidenceError("the current GLAZE UI V1.2 target must remain required")
    application_accepted = require_bool(
        acceptance["application_specific_acceptance_complete"],
        "acceptance.application_specific_acceptance_complete",
    )

    integrations = require_object(
        data["integral_platform_integrations"], "integral_platform_integrations"
    )
    require_exact_keys(integrations, INTEGRATIONS, "integral_platform_integrations")
    for system in sorted(INTEGRATIONS):
        item = require_object(integrations[system], f"integral_platform_integrations.{system}")
        require_exact_keys(
            item,
            {"applicability", "current_evidence_valid", "evidence_references"},
            f"integral_platform_integrations.{system}",
        )
        applicability = item["applicability"]
        if applicability not in {"applicable", "not_applicable"}:
            raise EvidenceError(f"{system} applicability is invalid")
        evidence_valid = require_bool(
            item["current_evidence_valid"], f"{system}.current_evidence_valid"
        )
        references = require_references(
            item["evidence_references"],
            f"{system}.evidence_references",
            required=applicability == "applicable",
            max_items=MAX_INTEGRATION_REFERENCES,
        )
        if applicability == "not_applicable" and (evidence_valid or references):
            raise EvidenceError(
                f"{system} marked not_applicable must not claim current integration evidence"
            )
        if accepted and applicability == "applicable" and not evidence_valid:
            raise EvidenceError(
                f"accepted Glaze claim requires current valid {system} integration evidence"
            )

    require_references(
        data["evidence_references"],
        "evidence_references",
        required=True,
        max_items=MAX_EVIDENCE_REFERENCES,
    )
    if accepted and not application_accepted:
        raise EvidenceError(
            "accepted Glaze claim requires application-specific acceptance to be complete"
        )
    return data


def load_record(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"evidence file is unreadable or invalid JSON: {exc}") from exc
    return validate_record(raw)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path, help="GLAZE UI V1.2 evidence JSON file")
    args = parser.parse_args()
    try:
        load_record(args.evidence)
    except EvidenceError as exc:
        parser.exit(1, f"Glaze UI evidence validation failed: {exc}\n")
    print(f"GLAZE UI V1.2 evidence validation passed: {args.evidence}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

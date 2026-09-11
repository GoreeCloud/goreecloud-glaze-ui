#!/usr/bin/env python3
from __future__ import annotations

import copy
import unittest
from datetime import UTC, datetime, timedelta

from validate_conformance_evidence import EvidenceError, validate_record

NOW = datetime(2026, 9, 11, 15, 45, tzinfo=UTC)
REVISION = "a" * 40


def integration(applicable: bool = True, valid: bool = True) -> dict[str, object]:
    if not applicable:
        return {
            "applicability": "not_applicable",
            "current_evidence_valid": False,
            "evidence_references": [],
        }
    return {
        "applicability": "applicable",
        "current_evidence_valid": valid,
        "evidence_references": ["evidence://integration/current"],
    }


def valid_record() -> dict[str, object]:
    return {
        "schema_version": 3,
        "producer": {"system": "goreecloud-acceptance", "authoritative": True},
        "target": {
            "application": "example-app",
            "glaze_version": "1.3.0",
            "source_revision": REVISION,
            "form_factors": ["mobile", "desktop"],
        },
        "observed_at": NOW.isoformat(),
        "valid_until": (NOW + timedelta(days=7)).isoformat(),
        "claim": {"kind": "conformance", "accepted": True},
        "acceptance": {
            "current_stable_required": True,
            "application_specific_acceptance_complete": True,
        },
        "integral_platform_integrations": {
            "manager": integration(),
            "identity": integration(),
            "privacy_shield": integration(),
            "wardveil_security": integration(),
            "everkeep": integration(),
            "goreecloud_mesh": integration(),
        },
        "evidence_references": ["evidence://glaze/current"],
    }


class EvidenceValidityTests(unittest.TestCase):
    def test_accepts_current_complete_evidence(self) -> None:
        record = valid_record()
        self.assertEqual(validate_record(record, now=NOW), record)

    def test_rejects_wrong_glaze_product_version(self) -> None:
        record = valid_record()
        record["target"]["glaze_version"] = "1.2.0"  # type: ignore[index]
        with self.assertRaisesRegex(EvidenceError, "current GLAZE UI V1.3 product version"):
            validate_record(record, now=NOW)

    def test_requires_manager_integration_evaluation(self) -> None:
        record = valid_record()
        del record["integral_platform_integrations"]["manager"]  # type: ignore[index]
        with self.assertRaisesRegex(EvidenceError, "manager"):
            validate_record(record, now=NOW)

    def test_rejects_expired_evidence(self) -> None:
        record = valid_record()
        record["observed_at"] = (NOW - timedelta(days=1)).isoformat()
        record["valid_until"] = (NOW - timedelta(seconds=1)).isoformat()
        with self.assertRaisesRegex(EvidenceError, "expired"):
            validate_record(record, now=NOW)

    def test_rejects_future_observation(self) -> None:
        record = valid_record()
        record["observed_at"] = (NOW + timedelta(seconds=1)).isoformat()
        record["valid_until"] = (NOW + timedelta(days=1)).isoformat()
        with self.assertRaisesRegex(EvidenceError, "must not be in the future"):
            validate_record(record, now=NOW)

    def test_rejects_non_rfc3339_datetime_separator(self) -> None:
        record = valid_record()
        record["observed_at"] = NOW.isoformat().replace("T", " ", 1)
        with self.assertRaisesRegex(EvidenceError, "RFC 3339"):
            validate_record(record, now=NOW)

    def test_accepts_rfc3339_z_suffix(self) -> None:
        record = valid_record()
        record["observed_at"] = "2026-09-11T15:45:00Z"
        self.assertEqual(validate_record(record, now=NOW), record)

    def test_rejects_accepted_claim_without_application_acceptance(self) -> None:
        record = valid_record()
        record["acceptance"]["application_specific_acceptance_complete"] = False  # type: ignore[index]
        with self.assertRaisesRegex(EvidenceError, "application-specific acceptance"):
            validate_record(record, now=NOW)

    def test_rejects_accepted_claim_with_stale_integral_system_evidence(self) -> None:
        record = valid_record()
        record["integral_platform_integrations"]["wardveil_security"][  # type: ignore[index]
            "current_evidence_valid"
        ] = False
        with self.assertRaisesRegex(EvidenceError, "wardveil_security"):
            validate_record(record, now=NOW)

    def test_not_applicable_system_cannot_carry_acceptance_evidence(self) -> None:
        record = valid_record()
        record["integral_platform_integrations"]["everkeep"] = integration(False)  # type: ignore[index]
        validate_record(record, now=NOW)
        invalid = copy.deepcopy(record)
        invalid["integral_platform_integrations"]["everkeep"][  # type: ignore[index]
            "current_evidence_valid"
        ] = True
        with self.assertRaisesRegex(EvidenceError, "not_applicable"):
            validate_record(invalid, now=NOW)

    def test_rejects_unknown_fields_and_bad_revision(self) -> None:
        record = valid_record()
        record["unexpected"] = True
        with self.assertRaisesRegex(EvidenceError, "unknown field"):
            validate_record(record, now=NOW)

        record = valid_record()
        record["target"]["source_revision"] = "abc"  # type: ignore[index]
        with self.assertRaisesRegex(EvidenceError, "40-character SHA"):
            validate_record(record, now=NOW)

    def test_enforces_schema_name_bounds(self) -> None:
        record = valid_record()
        record["producer"]["system"] = "a" * 161  # type: ignore[index]
        with self.assertRaisesRegex(EvidenceError, "at most 160 characters"):
            validate_record(record, now=NOW)

        record = valid_record()
        record["target"]["application"] = "a" * 161  # type: ignore[index]
        with self.assertRaisesRegex(EvidenceError, "at most 160 characters"):
            validate_record(record, now=NOW)

    def test_enforces_schema_reference_limits(self) -> None:
        record = valid_record()
        record["integral_platform_integrations"]["identity"][  # type: ignore[index]
            "evidence_references"
        ] = [f"evidence://identity/{index}" for index in range(21)]
        with self.assertRaisesRegex(EvidenceError, "20-item evidence-reference limit"):
            validate_record(record, now=NOW)

        record = valid_record()
        record["evidence_references"] = [f"evidence://glaze/{index}" for index in range(51)]
        with self.assertRaisesRegex(EvidenceError, "50-item evidence-reference limit"):
            validate_record(record, now=NOW)


if __name__ == "__main__":
    unittest.main()

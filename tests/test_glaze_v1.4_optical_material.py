from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate_glaze_v1.4_optical_material.py"
SPEC = importlib.util.spec_from_file_location("validate_glaze_v1_4_optical_material", MODULE_PATH)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)

with (ROOT / "tokens" / "glaze-v1.4-optical-material.candidate.json").open(encoding="utf-8") as handle:
    BASE = json.load(handle)


class GlazeV14OpticalMaterialTests(unittest.TestCase):
    def test_candidate_contract_passes(self) -> None:
        validator.validate_candidate(copy.deepcopy(BASE))

    def test_stable_claim_is_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["releaseLifecycle"] = "stable"
        with self.assertRaises(SystemExit):
            validator.validate_candidate(candidate)

    def test_consumer_eligibility_is_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["consumerEligible"] = True
        with self.assertRaises(SystemExit):
            validator.validate_candidate(candidate)

    def test_v13_token_removal_claim_is_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["compatibility"]["v1_3TokensRemoved"] = True
        with self.assertRaises(SystemExit):
            validator.validate_candidate(candidate)

    def test_optical_value_outside_binding_range_is_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["opticalProfiles"]["standard"]["refraction"] = 0.9
        with self.assertRaises(SystemExit):
            validator.validate_candidate(candidate)

    def test_missing_component_profile_is_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        del candidate["componentProfiles"]["dialog"]
        with self.assertRaises(SystemExit):
            validator.validate_candidate(candidate)

    def test_unknown_component_optical_profile_is_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["componentProfiles"]["toast"]["opticalProfile"] = "unbounded"
        with self.assertRaises(SystemExit):
            validator.validate_candidate(candidate)

    def test_accessibility_fallback_cannot_be_disabled(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["opticalEngine"]["accessibilityMayForceSolidFallback"] = False
        with self.assertRaises(SystemExit):
            validator.validate_candidate(candidate)


if __name__ == "__main__":
    unittest.main()

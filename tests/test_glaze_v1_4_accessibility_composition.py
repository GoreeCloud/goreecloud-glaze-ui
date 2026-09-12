from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate_glaze_v1_4_accessibility_composition.py"
SPEC = importlib.util.spec_from_file_location("validate_glaze_v1_4_accessibility_composition", MODULE_PATH)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)

with (ROOT / "contracts" / "v1.4" / "accessibility-composition.candidate.json").open(encoding="utf-8") as handle:
    BASE = json.load(handle)


class GlazeV14AccessibilityCompositionTests(unittest.TestCase):
    def test_candidate_contract_passes(self) -> None:
        validator.validate_contract(copy.deepcopy(BASE))

    def test_stable_claim_is_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["releaseLifecycle"] = "stable"
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate)

    def test_consumer_eligibility_is_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["consumerEligible"] = True
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate)

    def test_single_profile_behavior_authority_is_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["compositionPolicy"]["legacySummaryProfileIsBehaviorAuthority"] = True
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate)

    def test_forced_colors_must_remain_independent(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["browserIntegration"]["forcedColorsPreservedAsIndependentRequirement"] = False
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate)

    def test_multiple_known_requirements_must_not_require_consumer_selection(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["browserIntegration"]["knownMultipleRequirementsRequireConsumerSelection"] = True
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate)

    def test_reduced_transparency_solid_path_is_required(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["compositionPolicy"]["reducedTransparencyForcesDesignedSolidMaterial"] = False
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate)

    def test_low_power_requirement_must_constrain_performance(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["compositionPolicy"]["lowPowerPerformanceConstrainsToEfficientLevel"] = False
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate)

    def test_privacy_invasive_dependency_is_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["privacyBoundary"]["requiresTelemetry"] = True
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate)

    def test_browser_qualification_claim_is_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["qualificationBoundary"]["browserMatrixQualificationEstablished"] = True
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate)


if __name__ == "__main__":
    unittest.main()

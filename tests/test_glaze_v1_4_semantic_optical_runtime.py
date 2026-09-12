from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate_glaze_v1_4_semantic_optical_runtime.py"
SPEC = importlib.util.spec_from_file_location("validate_glaze_v1_4_semantic_optical_runtime", MODULE_PATH)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)

with (ROOT / "contracts" / "v1.4" / "semantic-optical-runtime.candidate.json").open(encoding="utf-8") as handle:
    BASE = json.load(handle)
with (ROOT / "tokens" / "glaze-v1.4-optical-material.candidate.json").open(encoding="utf-8") as handle:
    OPTICAL = json.load(handle)


class GlazeV14SemanticOpticalRuntimeTests(unittest.TestCase):
    def test_candidate_contract_passes(self) -> None:
        validator.validate_contract(copy.deepcopy(BASE), copy.deepcopy(OPTICAL))

    def test_stable_claim_is_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["releaseLifecycle"] = "stable"
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate, copy.deepcopy(OPTICAL))

    def test_consumer_eligibility_is_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["consumerEligible"] = True
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate, copy.deepcopy(OPTICAL))

    def test_implicit_runtime_acceptance_is_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["resolutionContract"]["noImplicitAcceptance"] = False
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate, copy.deepcopy(OPTICAL))

    def test_unknown_capability_acceptance_is_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["capabilityRules"]["undeclaredCapabilitiesAccepted"] = True
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate, copy.deepcopy(OPTICAL))

    def test_semantic_role_must_reference_known_optical_profile(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["semanticMaterialRoles"]["glz.material.surface"]["opticalProfile"] = "unbounded"
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate, copy.deepcopy(OPTICAL))

    def test_reduced_transparency_solid_path_is_required(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["accessibilityProfiles"]["reduced-transparency"]["mode"] = "translucent-only"
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate, copy.deepcopy(OPTICAL))

    def test_remote_environmental_pixels_are_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["environmentalSampling"]["remotePixelTransmissionAllowed"] = True
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate, copy.deepcopy(OPTICAL))

    def test_persistent_environmental_history_is_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["environmentalSampling"]["persistentHistoryAllowed"] = True
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate, copy.deepcopy(OPTICAL))

    def test_screenshot_permission_dependency_is_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["environmentalSampling"]["generalScreenshotPermissionRequired"] = True
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate, copy.deepcopy(OPTICAL))

    def test_visual_layer_cannot_become_operational_authority(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["truthAuthority"]["visualLayerIsOperationalAuthority"] = True
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate, copy.deepcopy(OPTICAL))

    def test_wardveil_authority_cannot_be_reassigned(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["truthAuthority"]["authorities"]["security"] = "Glaze UI"
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate, copy.deepcopy(OPTICAL))

    def test_production_budget_claim_is_rejected(self) -> None:
        candidate = copy.deepcopy(BASE)
        candidate["performanceQualification"]["productionNumericBudgetsEstablished"] = True
        with self.assertRaises(SystemExit):
            validator.validate_contract(candidate, copy.deepcopy(OPTICAL))


if __name__ == "__main__":
    unittest.main()

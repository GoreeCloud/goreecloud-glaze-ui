#!/usr/bin/env python3
"""Validate staged GLAZE UI V1.3 Candidate qualification without lifecycle promotion."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STABLE = "1.2.0"
TARGET = "1.3.0-candidate"
PRODUCT = "GLAZE UI V1.3"
CANDIDATE = {
    "human-optical-and-icon-collision-qualification",
    "manual-assistive-technology-qualification",
    "physical-device-native-platform-qualification",
    "physical-device-production-performance-qualification",
    "native-personalization-adapter-qualification",
}
STABLE_ONLY = "stable-activation-and-source-namespace-cleanup"
ALL = CANDIDATE | {STABLE_ONLY}

def load(path: str): return json.loads((ROOT / path).read_text(encoding="utf-8"))
def sha40(value): return isinstance(value, str) and len(value) == 40 and all(ch in "0123456789abcdef" for ch in value)

def main() -> int:
    errors=[]
    def req(ok,msg):
        if not ok: errors.append(msg)
    for path in ["contracts/v1.3/qualification-readiness.candidate.json","contracts/v1.3/stable-readiness.plan.json","contracts/v1.3/qualification-matrix.json","contracts/v1.3/deferred-qualification.plan.json","contracts/v1.3/qualification-evidence.schema.json","contracts/v1.3/quality-rules.candidate.json","js/glaze-v1.3-qualification.candidate.mjs","tests/glaze-v1.3-qualification.test.mjs","tests/glaze-v1.3-qualification-cli.test.mjs","GLAZE_UI_V1_3_CANDIDATE.md","acceptance/v1.3-candidate.md","acceptance/v1.3-deferred-qualification.md","registry/lifecycle.json","VERSION"]:
        req((ROOT/path).is_file(),f"missing staged qualification authority: {path}")
    if errors:
        print("GLAZE UI V1.3 staged qualification validation FAILED:"); [print(f"- {e}") for e in errors]; return 1

    req((ROOT/"VERSION").read_text().strip()==STABLE,"qualification must preserve VERSION 1.2.0")
    lifecycle=load("registry/lifecycle.json")
    req(lifecycle.get("currentStable")==STABLE and lifecycle.get("currentOfficial")==STABLE,"V1.2 must remain Stable/current official")
    req(lifecycle.get("activeCandidate") is None,"Candidate must remain inactive before governed promotion")
    req(lifecycle.get("plannedNext")==TARGET,"plannedNext must remain 1.3.0-candidate")

    deferred=load("contracts/v1.3/deferred-qualification.plan.json")
    req(deferred.get("schemaVersion")==4,"deferred plan schemaVersion must be 4")
    req(set(deferred.get("candidateStageItems",[]))==CANDIDATE,"candidate-stage workstream set mismatch")
    req(set(deferred.get("stableStageItems",[]))=={STABLE_ONLY},"Stable-stage workstream set mismatch")
    req(set(deferred.get("allStablePromotionItems",[]))==ALL,"all Stable-promotion workstreams mismatch")
    rules=deferred.get("rules",{})
    for key in ["freshExactRevisionEvidenceRequired","candidateStageMustPassSameExactRevision","stableCleanupOccursAfterCandidateActivation","stableCleanupMayTargetLaterExactRevision","stableCleanupMustReferenceQualifiedCandidateRevision","allSixRequiredBeforeStablePromotion","passedEvidenceAllowedDuringQualificationActive","qualificationReadinessDoesNotPromoteLifecycle"]: req(rules.get(key) is True,f"deferred staged rule must be true: {key}")
    req(rules.get("v1.3LifecyclePromotionAutomatic") is False,"qualification must never auto-promote lifecycle")

    matrix=load("contracts/v1.3/qualification-matrix.json")
    req(matrix.get("schemaVersion")==3,"qualification matrix schemaVersion must be 3")
    workstreams={item.get("id"):item for item in matrix.get("workstreams",[])}
    req(set(workstreams)==ALL,"matrix workstream IDs mismatch")
    req(all(workstreams[x].get("blockingForCandidatePromotion") is True and workstreams[x].get("blockingForStablePromotion") is True and workstreams[x].get("stage")=="pre-candidate" for x in CANDIDATE),"first five tracks must block Candidate and Stable")
    stable_item=workstreams.get(STABLE_ONLY,{})
    req(stable_item.get("blockingForCandidatePromotion") is False,"Stable cleanup must not block Candidate promotion")
    req(stable_item.get("blockingForStablePromotion") is True and stable_item.get("stage")=="post-candidate-pre-stable","Stable cleanup must block Stable after Candidate")

    contract=load("contracts/v1.3/qualification-readiness.candidate.json")
    req(contract.get("schemaVersion")==2,"Candidate readiness schemaVersion must be 2")
    req({x.get("id") for x in contract.get("requiredWorkstreams",[])}==CANDIDATE,"Candidate readiness must require exactly five tracks")
    deferred_stable=contract.get("deferredUntilPostCandidate",{})
    req(deferred_stable.get("workstreamId")==STABLE_ONLY and deferred_stable.get("blockingForCandidatePromotion") is False and deferred_stable.get("blockingForStablePromotion") is True,"Candidate contract must explicitly defer Stable cleanup")
    record=contract.get("recordAcceptance",{})
    req(record.get("singleSharedExactRevisionRequiredForCandidateStage") is True,"five Candidate tracks must share one exact revision")

    stable=load("contracts/v1.3/stable-readiness.plan.json")
    req(stable.get("stage")=="post-candidate-pre-stable","Stable readiness must be post-Candidate")
    req(stable.get("prerequisites",{}).get("activeCandidateRequired") is True,"Stable stage must require active Candidate")
    stable_ws=stable.get("stableStageWorkstream",{})
    req(stable_ws.get("id")==STABLE_ONLY and stable_ws.get("mayDifferFromQualifiedCandidateSourceRevision") is True and stable_ws.get("mustReferenceQualifiedCandidateSourceRevision") is True,"Stable cleanup must use later exact revision with Candidate provenance")
    req(stable.get("stablePromotion",{}).get("allSixQualificationRequirementsMandatoryAcrossStages") is True,"all six requirements must remain mandatory before Stable")
    req(stable.get("stablePromotion",{}).get("automatic") is False,"Stable promotion must remain governed")

    schema=load("contracts/v1.3/qualification-evidence.schema.json")
    req(set(schema.get("properties",{}).get("workstream_id",{}).get("enum",[]))==ALL,"evidence schema must continue supporting all six tracks")
    quality=load("contracts/v1.3/quality-rules.candidate.json")
    req(len(quality.get("rules",[]))==55 and quality.get("humanReviewRequired") is True and quality.get("automatedValidationSufficient") is False,"55-rule human quality authority must remain intact")

    accepted_candidate_revisions=set()
    for path in sorted((ROOT/"evidence/v1.3").glob("*.json")):
        value=json.loads(path.read_text())
        req(value.get("workstream_id") in ALL,f"{path.name}: unknown workstream")
        target=value.get("target",{})
        req(target.get("product")==PRODUCT and target.get("target_version")==TARGET,f"{path.name}: target mismatch")
        revision=target.get("source_revision"); req(sha40(revision),f"{path.name}: invalid source revision")
        accepted=value.get("status")=="passed" and value.get("disposition",{}).get("accepted_for_lifecycle_gate") is True
        if accepted and value.get("workstream_id") in CANDIDATE: accepted_candidate_revisions.add(revision)
        if value.get("status")!="passed": req(value.get("disposition",{}).get("accepted_for_lifecycle_gate") is not True,f"{path.name}: non-passed evidence cannot be lifecycle-accepted")
    req(len(accepted_candidate_revisions)<=1,"accepted pre-Candidate evidence may not mix exact revisions")

    doc=(ROOT/"GLAZE_UI_V1_3_CANDIDATE.md").read_text()
    req("five pre-Candidate" in doc and "post-Candidate" in doc,"Candidate package must describe staged qualification")
    req("Candidate is NOT active" in doc,"Candidate package must preserve inactive lifecycle")
    acceptance=(ROOT/"acceptance/v1.3-candidate.md").read_text()
    req("**Status:** BLOCKED" in acceptance and "**No promotion decision is recorded.**" in acceptance,"Candidate ledger must remain blocked without real evidence")
    req(not (ROOT/"css/glaze-v1.3.0-candidate.css").exists() and not (ROOT/"js/glaze-v1.3.0-candidate.mjs").exists(),"Candidate entrypoints must not exist before formal promotion")

    if errors:
        print("GLAZE UI V1.3 staged qualification validation FAILED:"); [print(f"- {e}") for e in errors]; return 1
    print("GLAZE UI V1.3 staged qualification mechanism: PASS")
    print("Outcome: five-track Candidate gate and post-Candidate Stable cleanup are separated; lifecycle remains unpromoted.")
    return 0
if __name__ == "__main__": raise SystemExit(main())

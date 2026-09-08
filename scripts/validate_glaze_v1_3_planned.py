#!/usr/bin/env python3
"""Validate GLAZE UI V1.3 qualification control-plane authority and visual-quality invariants."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PRODUCT="GLAZE UI V1.3"; TARGET="1.3.0-candidate"; STABLE="1.2.0"; QUALITY="contracts/v1.3/quality-rules.candidate.json"
CANDIDATE={"human-optical-and-icon-collision-qualification","manual-assistive-technology-qualification","physical-device-native-platform-qualification","physical-device-production-performance-qualification","native-personalization-adapter-qualification"}
STABLE_ONLY="stable-activation-and-source-namespace-cleanup"; ALL=CANDIDATE|{STABLE_ONLY}; RULE_IDS={f"quality-{i:02d}" for i in range(1,56)}
def load(path): return json.loads((ROOT/path).read_text(encoding="utf-8"))
def main():
    errors=[]
    def req(ok,msg):
        if not ok: errors.append(msg)
    req((ROOT/"VERSION").read_text().strip()==STABLE,"V1.3 qualification must preserve VERSION 1.2.0")
    lifecycle=load("registry/lifecycle.json"); req(lifecycle.get("currentStable")==STABLE and lifecycle.get("currentOfficial")==STABLE and lifecycle.get("activeCandidate") is None,"V1.2 Stable authority and inactive Candidate boundary must hold")
    for path in ["acceptance/v1.3-deferred-qualification.md","contracts/v1.3/deferred-qualification.plan.json","contracts/v1.3/qualification-matrix.json","contracts/v1.3/qualification-evidence.schema.json","contracts/v1.3/qualification-readiness.candidate.json","contracts/v1.3/stable-readiness.plan.json",QUALITY,"evidence/v1.3/README.md"]: req((ROOT/path).is_file(),f"missing V1.3 authority: {path}")
    if errors: [print(f"- {e}") for e in errors]; return 1
    plan=load("contracts/v1.3/deferred-qualification.plan.json"); req(plan.get("schemaVersion")==4 and plan.get("lifecycle")=="qualification-active","deferred control plane must be schema 4 / qualification-active"); req(set(plan.get("candidateStageItems",[]))==CANDIDATE and set(plan.get("stableStageItems",[]))=={STABLE_ONLY} and set(plan.get("allStablePromotionItems",[]))==ALL,"deferred staged workstream sets mismatch")
    matrix=load("contracts/v1.3/qualification-matrix.json"); req(matrix.get("schemaVersion")==3,"matrix schemaVersion must be 3"); items={x.get("id"):x for x in matrix.get("workstreams",[]) if isinstance(x,dict)}; req(set(items)==ALL,"matrix must contain all six workstreams"); req(sum(1 for x in items.values() if x.get("blockingForCandidatePromotion") is True)==5,"exactly five workstreams must block Candidate promotion"); req(sum(1 for x in items.values() if x.get("blockingForStablePromotion") is True)==6,"all six workstreams must block Stable promotion")
    rules=matrix.get("globalRules",{}); required_true=["v1.2EvidenceMayNotBeReclassifiedAsV1.3Pass","exactSourceRevisionRequired","allCandidateBlockingWorkstreamsMustPassBeforeCandidatePromotion","candidateBlockingWorkstreamsMustPassSameExactRevision","allStableBlockingWorkstreamsMustPassBeforeStablePromotion","stableCleanupOccursAfterCandidateActivation","stableCleanupMayTargetLaterExactRevisionThanCandidateQualification","stablePromotionRequiresCandidateQualificationProvenance","qualificationReadinessDoesNotPromoteLifecycle","humanOpticalPassRequiresFullQualityRuleCoverage","automatedValidationDoesNotReplaceHumanReview","consumerEligibilityIsSeparate","downstreamProductionAcceptanceIsSeparate","plannedStatusIsNotEvidence"]; [req(rules.get(k) is True,f"matrix rule must be true: {k}") for k in required_true]
    quality=load(QUALITY); qrules=quality.get("rules",[]); req(len(qrules)==55 and {x.get("id") for x in qrules if isinstance(x,dict)}==RULE_IDS,"quality contract must contain exactly quality-01 through quality-55"); req(quality.get("humanReviewRequired") is True and quality.get("automatedValidationSufficient") is False,"human quality review must remain mandatory")
    schema=load("contracts/v1.3/qualification-evidence.schema.json"); props=schema.get("properties",{}); req(props.get("schema_version",{}).get("const")==2,"evidence schema_version must remain 2"); req(set(props.get("workstream_id",{}).get("enum",[]))==ALL,"evidence schema must support all six workstreams"); qschema=props.get("quality_review",{}).get("properties",{}).get("reviewed_rule_ids",{}); req(qschema.get("minItems")==55 and qschema.get("maxItems")==55,"human optical evidence must require exactly 55 rule IDs")
    stable=load("contracts/v1.3/stable-readiness.plan.json"); req(stable.get("stage")=="post-candidate-pre-stable" and stable.get("prerequisites",{}).get("activeCandidateRequired") is True,"Stable stage must be post-Candidate"); req(stable.get("stablePromotion",{}).get("allSixQualificationRequirementsMandatoryAcrossStages") is True and stable.get("stablePromotion",{}).get("automatic") is False,"all six must remain mandatory before governed Stable promotion")
    if errors:
        print("GLAZE UI V1.3 qualification control-plane validation FAILED:"); [print(f"- {e}") for e in errors]; return 1
    print("GLAZE UI V1.3 qualification control plane: PASS")
    print("Candidate readiness is a five-track exact-revision gate; the sixth Stable cleanup gate is post-Candidate and all six remain required before Stable.")
    return 0
if __name__=="__main__": raise SystemExit(main())

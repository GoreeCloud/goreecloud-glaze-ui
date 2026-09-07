#!/usr/bin/env python3
"""Validate the fail-closed GLAZE UI V1.3 post-Candidate Stable-readiness mechanism."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STABLE_ONLY="stable-activation-and-source-namespace-cleanup"
def load(path): return json.loads((ROOT/path).read_text(encoding="utf-8"))
def main():
    errors=[]
    def req(ok,msg):
        if not ok: errors.append(msg)
    required=["contracts/v1.3/stable-readiness.plan.json","contracts/v1.3/qualification-readiness.candidate.json","contracts/v1.3/qualification-matrix.json","js/glaze-v1.3-stable-readiness.candidate.mjs","scripts/evaluate_glaze_v1_3_stable_readiness.mjs","tests/glaze-v1.3-stable-readiness.test.mjs","registry/lifecycle.json","VERSION"]
    for path in required: req((ROOT/path).is_file(),f"missing Stable-readiness artifact: {path}")
    if errors: [print(f"- {e}") for e in errors]; return 1
    plan=load("contracts/v1.3/stable-readiness.plan.json"); req(plan.get("schemaVersion")==2,"Stable plan schemaVersion must be 2"); req(plan.get("stage")=="post-candidate-pre-stable","Stable readiness must be post-Candidate/pre-Stable"); req(plan.get("lifecycleAuthority") is False,"Stable readiness mechanism must not own lifecycle"); req(plan.get("readinessEvaluator")=="js/glaze-v1.3-stable-readiness.candidate.mjs","Stable evaluator authority mismatch"); prereq=plan.get("prerequisites",{}); req(prereq.get("activeCandidateRequired") is True and prereq.get("candidateQualificationGateRequired") is True and prereq.get("candidateQualificationWorkstreamCount")==5,"Stable readiness must require an active, five-track-qualified Candidate"); ws=plan.get("stableStageWorkstream",{}); req(ws.get("id")==STABLE_ONLY and ws.get("mustRunAfterCandidateActivation") is True and ws.get("exactStablePromotionSourceRevisionRequired") is True and ws.get("mustReferenceQualifiedCandidateSourceRevision") is True,"Stable cleanup sequencing/provenance rules incomplete"); req(set(ws.get("requiredEnvironmentFields",[]))=={"qualified_candidate_source_revision","stable_promotion_source_revision","candidate_lifecycle_observed","equivalence_review_completed","import_closure_validated","rollback_verified"},"Stable cleanup required environment fields mismatch"); promotion=plan.get("stablePromotion",{}); req(promotion.get("allSixQualificationRequirementsMandatoryAcrossStages") is True and promotion.get("formalLifecycleDecisionRequired") is True and promotion.get("automatic") is False and promotion.get("consumerConformanceAutomatic") is False,"Stable promotion must remain six-requirement, governed and non-automatic")
    lifecycle=load("registry/lifecycle.json"); req((ROOT/"VERSION").read_text().strip()=="1.2.0" and lifecycle.get("currentStable")=="1.2.0" and lifecycle.get("currentOfficial")=="1.2.0","mechanism implementation must preserve V1.2 Stable authority"); req(lifecycle.get("activeCandidate") is None,"current repository truth must still show no active Candidate"); req(not (ROOT/"css/glaze-v1.3.0.css").exists() and not (ROOT/"js/glaze-v1.3.0.mjs").exists(),"Stable mechanism must not create Stable entrypoints prematurely")
    runtime=(ROOT/"js/glaze-v1.3-stable-readiness.candidate.mjs").read_text(); [req(symbol in runtime,f"Stable runtime missing API: {symbol}") for symbol in ["evaluateStableReadiness","STABLE_CLEANUP_WORKSTREAM","stableReadinessCandidate"]]; [req(token not in runtime,f"Stable runtime contains forbidden side-effect primitive: {token}") for token in ["fetch(","XMLHttpRequest","sendBeacon","WebSocket(","localStorage","sessionStorage","indexedDB","child_process","node:fs"]]
    if errors:
        print("GLAZE UI V1.3 Stable-readiness validation FAILED:"); [print(f"- {e}") for e in errors]; return 1
    print("GLAZE UI V1.3 Stable-readiness mechanism: PASS")
    print("Boundary: active Candidate + five-track provenance + exact later Stable cleanup are required; no Stable promotion is granted.")
    return 0
if __name__=="__main__": raise SystemExit(main())

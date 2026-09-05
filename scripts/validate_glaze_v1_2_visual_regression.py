#!/usr/bin/env python3
"""Source validation for bounded V1.2 provisional visual regression."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"contracts/v1.2/visual-regression.candidate.json"
HARNESS=ROOT/"scripts/glaze_v1_2_visual_regression.py"
WORKFLOW=ROOT/".github/workflows/glaze-v1.2-visual-regression.yml"
REFERENCE_INDEX=ROOT/"contracts/v1.2/reference-scenes.candidate.json"
STABLE_BASELINE=ROOT/"contracts/regression/visual-baselines-v1.json"
FUTURE_INVARIANTS=ROOT/"contracts/regression/reference-invariants.json"
PROVISIONAL_REFERENCE="a20ff9dacab9a83bfc58473a0b124f61f47af7c5"
EXPECTED_COVERAGE=["light","dark","deep-dark","mobile","typography","icons","component-state","reduced-transparency","increased-contrast","large-text","rtl"]
EXPECTED_SCENES=[
"system-shell-light-1440x1000-default-web","system-shell-dark-1440x1000-default-web","system-shell-deep-dark-1440x1000-default-web","system-shell-light-390x844-mobile-web","typography-light-1280x960-default-web","typography-light-390x844-text-200-web","crystal-icons-light-1280x960-reduced-motion-web","interaction-states-light-1280x1200-reduced-motion-web","system-shell-light-1440x1000-reduced-transparency-web","states-light-1280x960-increased-contrast-web","responsive-rtl-1280x960-default-web"]

class ValidationError(RuntimeError): pass
def require(ok:bool,message:str)->None:
    if not ok: raise ValidationError(message)
def load(path:Path)->dict[str,Any]:
    require(path.is_file(),f"missing {path.relative_to(ROOT)}")
    value=json.loads(path.read_text(encoding="utf-8")); require(isinstance(value,dict),f"expected object in {path.relative_to(ROOT)}"); return value

def validate_contract()->dict[str,Any]:
    c=load(CONTRACT)
    require(c.get("schemaVersion")==1 and c.get("id")=="glaze-v1.2-visual-regression-candidate","visual regression identity drifted")
    require(c.get("product")=="GLAZE UI" and c.get("version")=="1.2.0-candidate" and c.get("lifecycle")=="candidate" and c.get("consumerEligible") is False,"Candidate boundary drifted")
    require(c.get("stableBaseline")=="1.1.0" and c.get("status")=="bounded-provisional-zero-drift-regression","Stable/bounded status drifted")
    authority=c.get("authority",{})
    require(authority.get("referenceSceneIndex")=="contracts/v1.2/reference-scenes.candidate.json","reference-scene authority drifted")
    require(authority.get("immutableStableBaseline")=="contracts/regression/visual-baselines-v1.json" and authority.get("unrelatedFutureRegressionAuthority")=="contracts/regression/reference-invariants.json","regression authority boundary drifted")
    ref=c.get("provisionalReference",{})
    require(ref.get("revision")==PROVISIONAL_REFERENCE and ref.get("verifiedExactHeadWorkflowCount")==30,"provisional reference drifted")
    require(ref.get("humanApproved") is False and ref.get("canonicalScreenshotBaseline") is False and ref.get("acceptanceAuthority") is False,"provisional reference overclaimed authority")
    comparison=c.get("comparison",{})
    require(comparison.get("mode")=="decoded-pixel-zero-drift" and comparison.get("changedPixelTolerance")==0 and comparison.get("maximumChannelDeltaTolerance")==0,"zero-drift rule drifted")
    require(comparison.get("pixelDifferenceAloneIsHumanAcceptanceAuthority") is False and comparison.get("humanOpticalReviewRemainsAuthoritative") is True,"human optical authority drifted")
    env=c.get("captureEnvironment",{})
    for key in ("sameRunnerRequired","viewportPinnedPerScene","fontReadinessRequired","animationsDisabledForCapture","transitionsDisabledForCapture","caretHiddenForCapture","scrollPositionPinnedToTop"): require(env.get(key) is True,f"capture stabilization drifted: {key}")
    require(env.get("devicePixelRatio")==1 and env.get("remoteRuntimeAssetsAllowed") is False,"capture environment boundary drifted")
    require(c.get("requiredCoverage")==EXPECTED_COVERAGE,"coverage set/order drifted")
    scenes=c.get("scenes",[]); require(isinstance(scenes,list) and [s.get("id") for s in scenes if isinstance(s,dict)]==EXPECTED_SCENES,"scene set/order drifted")
    covered:set[str]=set()
    for scene in scenes:
        require(isinstance(scene,dict),"scene must be object"); page=scene.get("page"); viewport=scene.get("viewport")
        require(isinstance(page,str) and page.startswith("reference/v1.2/") and (ROOT/page).is_file(),f"scene page invalid: {page}")
        require(isinstance(viewport,list) and len(viewport)==2 and all(isinstance(x,int) and x>0 for x in viewport),f"scene viewport invalid: {scene.get('id')}")
        coverage=scene.get("coverage"); require(isinstance(coverage,list) and coverage,f"scene coverage missing: {scene.get('id')}"); covered.update(str(x) for x in coverage)
        require(isinstance(scene.get("readyExpression"),str) and scene.get("readyExpression"),f"ready expression missing: {scene.get('id')}")
    require(covered==set(EXPECTED_COVERAGE),f"coverage mismatch: {sorted(covered)}")
    policy=c.get("baselineUpdatePolicy",{})
    for key in ("baselineChangeIsDesignChange","explicitReasonRequired","affectedRegionsRequired","reviewedScreenshotsRequired","ownerApprovalRequired","approverAndDateTraceabilityRequired","referenceRevisionMustBeExact","latestOrCurrentAliasProhibited","intentionalOpticalChangeMustFailOldReferenceUntilReviewedReferenceAdvance"): require(policy.get(key) is True,f"baseline update policy drifted: {key}")
    boundaries=c.get("boundaries",{})
    for key in ("v11HumanApprovedBaselineMayBeMutated","v11HumanApprovedBaselineCountsAsV12Baseline","v21CandidateInvariantsCountAsV12Authority","provisionalReferenceCountsAsHumanOpticalAcceptance","provisionalReferenceCountsAsReleaseAcceptance","automatedRegressionReplacesHumanReview","applicationIconEcosystemWallCovered","referenceScenesComplete"): require(boundaries.get(key) is False,f"authority boundary drifted: {key}")
    require(boundaries.get("consumerClaimBlocked") is True,"consumer claim boundary drifted")
    for item in ("human-approved-v1.2-canonical-screenshot-baseline","final-perceptual-visual-difference-thresholds","application-icon-ecosystem-wall-regression","human-optical-acceptance","native-platform-visual-regression","release-candidate","stable","consumer-conformance"): require(item in c.get("notEstablished",[]),f"not-established boundary missing: {item}")
    return c

def validate_authorities()->None:
    index=load(REFERENCE_INDEX); require(index.get("version")=="1.2.0-candidate" and index.get("boundedEstablishedCount")==15 and index.get("requiredSceneCount")==16 and index.get("phase5ReferenceScenesComplete") is False and index.get("openSceneIds")==["application-icon-ecosystem-wall"],"reference-scene boundary drifted")
    stable=load(STABLE_BASELINE); require(stable.get("product")=="GLAZE UI V1.1" and stable.get("version")=="1.1.0" and stable.get("status")=="stable-human-approved-source-pinned" and stable.get("newOpticalPixelsRequireNewHumanApproval") is True,"immutable V1.1 baseline drifted")
    future=load(FUTURE_INVARIANTS); require(future.get("id")=="glaze-ui-2.1-reference-regression" and future.get("lifecycle")=="candidate" and future.get("since")=="2.1.0-candidate.1","2.1 regression boundary drifted")

def validate_harness_workflow(c:dict[str,Any])->None:
    require(HARNESS.is_file(),"visual regression harness missing"); harness=HARNESS.read_text(encoding="utf-8")
    for marker in ("Emulation.setDeviceMetricsOverride","deviceScaleFactor","document.fonts.status","animation:none!important","transition:none!important","caret-color:transparent!important","decode_png","changedPixels","provisionalReferenceRevision"): require(marker in harness,f"harness marker missing: {marker}")
    for forbidden in ("import PIL","import cv2","import numpy","import requests","import selenium"): require(forbidden not in harness,f"unexpected third-party runtime dependency: {forbidden}")
    require(WORKFLOW.is_file(),"visual regression workflow missing"); workflow=WORKFLOW.read_text(encoding="utf-8"); reference=c["provisionalReference"]["revision"]
    for marker in ("Glaze V1.2 Provisional Visual Regression Candidate","github.event.pull_request.head.sha || github.sha","persist-credentials: false",reference,"path: _visual-reference","python scripts/validate_glaze_v1_2_visual_regression.py","glaze_v1_2_visual_regression.py capture","glaze_v1_2_visual_regression.py compare","if: always()"): require(marker in workflow,f"workflow marker missing: {marker}")

def main()->int:
    try:
        c=validate_contract(); validate_authorities(); validate_harness_workflow(c)
    except (ValidationError,OSError,json.JSONDecodeError) as error:
        print(f"FAIL: {error}"); return 1
    print("PASS: V1.2 provisional visual regression is source-pinned, deterministic, and non-authoritative; human optical approval remains open."); return 0
if __name__=="__main__": raise SystemExit(main())

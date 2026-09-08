# GLAZE UI V1.3 — Adaptive Resonance Candidate Qualification Package

**Lifecycle:** Proposed — **Candidate is NOT active**  
**Qualification state:** Active / blocked pending fresh accepted evidence  
**Planned machine target:** `1.3.0-candidate`  
**Stable baseline:** GLAZE UI V1.2 / `1.2.0`  
**Consumer eligible:** No  
**Lifecycle effect of this document:** None

This package defines the final pre-Candidate qualification boundary. Its filename does not activate Candidate; `registry/lifecycle.json` remains authoritative and V1.2 remains current Stable/current official while `activeCandidate` is `null`.

## 1. Staged release ladder

Qualification is intentionally staged so lifecycle promotion is not circular:

1. **Pre-Candidate qualification:** five fresh human/manual/physical/native tracks must pass for one identical exact V1.3 source revision.
2. **Governed Candidate promotion:** a separate repository change may activate `1.3.0-candidate` only after the five-track gate is satisfied and explicitly reviewed.
3. **Post-Candidate Stable qualification:** `stable-activation-and-source-namespace-cleanup` runs against the later exact Stable-promotion source revision and must reference the qualified Candidate revision.
4. **Governed Stable promotion:** all six qualification requirements across both stages must be satisfied before V1.3 can become Stable.

Fresh qualification may satisfy a lifecycle gate; it may not perform lifecycle promotion.

## 2. Five pre-Candidate qualification tracks

The Candidate readiness evaluator requires:

1. `human-optical-and-icon-collision-qualification`
2. `manual-assistive-technology-qualification`
3. `physical-device-native-platform-qualification`
4. `physical-device-production-performance-qualification`
5. `native-personalization-adapter-qualification`

All five accepted records must target the same exact 40-character source revision. V1.2 evidence may not be relabeled as V1.3 evidence. Human optical acceptance must cover all 55 governed visual-quality rules.

## 3. Sixth Stable qualification track

`stable-activation-and-source-namespace-cleanup` is **not** a pre-Candidate prerequisite. It is a post-Candidate/pre-Stable requirement covering Candidate-name inventory, migration mapping, byte/pixel/behavior equivalence, import closure, rollback, and human/automated review. Its exact source revision may be later than the Candidate qualification revision because Candidate activation and cleanup themselves are governed source changes. It must preserve explicit provenance back to the qualified Candidate revision.

This sequencing change does not weaken Stable qualification: all six requirements remain mandatory before Stable.

## 4. Evidence acceptance rules

Evidence records live under `evidence/v1.3/` and conform to `contracts/v1.3/qualification-evidence.schema.json`. A record contributes only when it is fresh, `passed`, explicitly accepted for its lifecycle gate, independently inspectable, uses the required review authority, is unexpired, has no unresolved issues, and targets an exact immutable source revision.

Automation may validate evidence structure and readiness accounting. It may not manufacture human optical, manual assistive-technology, physical-device/native-platform, physical performance, native Personalization, or Stable cleanup/equivalence acceptance.

## 5. Candidate readiness evaluator

`js/glaze-v1.3-qualification.candidate.mjs` reports either `blocked` or `ready-for-governed-candidate-promotion-review` for the five pre-Candidate tracks. Even a ready result always leaves:

- `lifecyclePromotionGranted: false`;
- `candidateActivated: false`;
- `stablePromoted: false`;
- `consumerEligibilityGranted: false`;
- `consumerConformanceGranted: false`.

Stable readiness is governed separately by `contracts/v1.3/stable-readiness.plan.json`.

## 6. Current qualification state

The authoritative `evidence/v1.3/` directory contains no accepted V1.3 qualification records. Therefore the current Candidate qualification outcome is **blocked**. This is truthful release state, not an implementation failure.

## 7. Candidate activation prerequisites

A governed Candidate activation may be considered only after all implementation workstreams and Migration/Consumer Boundary remain validated, all five pre-Candidate qualification tracks have accepted fresh evidence for one exact revision, the evaluator reports readiness, V1.2 Stable authority remains intact immediately before promotion, and lifecycle/entrypoint/acceptance changes are reviewed and recorded explicitly.

## 8. Stable promotion boundary

Candidate activation does not make V1.3 Stable. Before Stable, the sixth post-Candidate cleanup/equivalence track must pass on its exact Stable-promotion revision with Candidate-revision provenance, every applicable Stable validation gate must pass, and an explicit governed Stable promotion must occur. Consumer conformance remains separate.

## 9. Current non-claims

This package does not establish an active Candidate, RC or Stable status; complete human/manual/physical/native qualification; Stable namespace cleanup acceptance; consumer eligibility; or downstream consumer conformance.

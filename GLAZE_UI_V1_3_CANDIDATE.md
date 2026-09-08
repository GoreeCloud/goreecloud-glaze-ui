# GLAZE UI V1.3 — Adaptive Resonance Candidate Qualification Package

> **Historical pre-promotion package.** This document preserves the Candidate qualification model and blocked evidence state that existed before the project-owner bounded V1.3.0 Stable promotion on 2026-09-07. It is no longer current lifecycle authority. Missing/pending evidence remains missing/pending and is carried to `acceptance/v1.3.1-hardening.md` rather than rewritten as passed.

**Lifecycle at record time:** Proposed — **Candidate was NOT active**  
**Qualification state at record time:** Active / blocked pending fresh accepted evidence  
**Planned machine target at record time:** `1.3.0-candidate`  
**Stable baseline at record time:** GLAZE UI V1.2 / `1.2.0`  
**Consumer eligible at record time:** No  
**Current lifecycle authority:** GLAZE UI V1.3 / `1.3.0` Stable via `VERSION`, `registry/lifecycle.json`, and `acceptance/v1.3-stable.md`

This package defined the final pre-Candidate qualification boundary before the later owner-governed Stable release decision. Its filename never activated Candidate; lifecycle authority always remained separate.

## 1. Historical staged release ladder

The pre-promotion qualification model was intentionally staged:

1. **Pre-Candidate qualification:** five fresh human/manual/physical/native tracks were intended to pass for one identical exact V1.3 source revision.
2. **Governed Candidate promotion:** a separate repository change could have activated `1.3.0-candidate` only after the five-track gate.
3. **Post-Candidate Stable qualification:** `stable-activation-and-source-namespace-cleanup` was intended to run against a later exact Stable-promotion revision with Candidate provenance.
4. **Governed Stable promotion:** the historical model required all six tracks before Stable.

On 2026-09-07 the project owner superseded this staged model **as the V1.3.0 lifecycle gate only**, directing bounded Stable promotion and transfer of unfinished qualification to V1.3.1. That decision did not convert any track to passed evidence.

## 2. Five historical pre-Candidate qualification tracks

The readiness evaluator tracked:

1. `human-optical-and-icon-collision-qualification`
2. `manual-assistive-technology-qualification`
3. `physical-device-native-platform-qualification`
4. `physical-device-production-performance-qualification`
5. `native-personalization-adapter-qualification`

The historical gate required all accepted records to target the same exact 40-character source revision. V1.2 evidence could not be relabeled as V1.3 evidence. Those truth constraints remain valid for any evidence later collected for hardening.

## 3. Sixth historical Stable qualification track

`stable-activation-and-source-namespace-cleanup` was the post-Candidate/pre-Stable track for Candidate-name inventory, migration mapping, byte/pixel/behavior equivalence, import closure, rollback, and human/automated review.

It did not complete as accepted V1.3 evidence before the bounded Stable decision. Equivalent cleanup/equivalence work is now H6 in `acceptance/v1.3.1-hardening.md`.

## 4. Evidence acceptance rules

Historical evidence records live under `evidence/v1.3/` and conform to `contracts/v1.3/qualification-evidence.schema.json`. Automation may validate evidence structure and readiness accounting, but it may not manufacture human optical, manual assistive-technology, physical-device/native-platform, physical performance, native Personalization, or cleanup/equivalence acceptance.

That fail-closed evidence rule remains in force after Stable promotion.

## 5. Historical readiness evaluator

`js/glaze-v1.3-qualification.candidate.mjs` is retained as a fail-closed historical/readiness policy evaluator. It never owns lifecycle authority and never grants consumer conformance. Current Stable status comes from the later governed lifecycle record, not from changing this evaluator's historical result.

## 6. Recorded qualification state

At the recorded pre-promotion gate, `evidence/v1.3/` contained no accepted V1.3 qualification records. The Candidate qualification outcome was therefore **blocked**.

That remains truthful historical evidence. V1.3.0 Stable is a later bounded lifecycle decision; the blocked result is not retroactively changed.

## 7. Current hardening handoff

All unresolved qualification obligations represented by this package are now maintained in `acceptance/v1.3.1-hardening.md`. V1.3.0 remains Stable while that maintenance backlog is open. A future V1.3.1 patch requires its own exact-revision validation and governed lifecycle decision.

## 8. Consumer boundary

V1.3.0 Stable is consumer-eligible, but no downstream consumer is automatically conformant or production-eligible. Each consumer must perform independent repository-local migration and acceptance against exact consumer and Glaze UI revisions.

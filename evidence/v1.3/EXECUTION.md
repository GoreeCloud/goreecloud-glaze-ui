# GLAZE UI V1.3 Fresh Qualification Execution

**Status:** Qualification preparation / no workstream pass recorded  
**Release lifecycle:** Proposed  
**Qualification lifecycle:** Qualification active  
**Stable authority:** GLAZE UI V1.2 / `1.2.0`

This runbook controls collection of fresh evidence for the six blocking GLAZE UI V1.3 qualification workstreams. It does not activate Candidate or grant consumer eligibility/conformance.

## 1. Establish the promotion-candidate source revision

Before human or physical-device review begins:

1. finish source-affecting implementation, quality-contract, qualification-tooling, and branch-reconciliation changes;
2. require green exact-head Phase 0, V1.2 Stable, Migration, Qualification Control Plane, Fresh Qualification, lifecycle-documentation, and consumer-registry CI;
3. select one exact lowercase 40-character Git SHA as the **promotion candidate revision**;
4. record that SHA in the qualification tracking issue and every evidence record;
5. do not silently retarget evidence after testing.

Evidence/reporting commits may be descendants of the tested source revision. Their records must continue to identify the exact source revision actually observed. Any source change that can affect an observation invalidates affected evidence and requires a new qualification round.

The previous frozen revision `2845c47b1f9a486b091aad1eda8cbd1136dc248f` is superseded by later source-affecting V1.3 quality, qualification, lifecycle-integrity, consumer-governance, and CI improvements. Its successful automated checks remain historical evidence only and must not be reused as exact-head qualification evidence for the next frozen source revision.

## 2. Evidence records

Accepted records live directly in `evidence/v1.3/*.json` and must conform to `contracts/v1.3/qualification-evidence.schema.json` using `schema_version: 2`.

Reviewer worksheets live under `evidence/v1.3/templates/`. They are preparation aids only and are deliberately not JSON qualification records.

A record contributes to readiness only when it is `passed`, explicitly accepted for the lifecycle gate, independently inspectable, unexpired, free of unresolved issues, and bound to the shared promotion-candidate SHA.

### Human optical visual-quality boundary

The `human-optical-and-icon-collision-qualification` pass must additionally bind to `contracts/v1.3/quality-rules.candidate.json` and record all `quality-01` through `quality-55` exactly once. It must explicitly accept:

- the Visual Finish Gate;
- the Blandness Rejection Gate;
- Accessibility Is Part of Beauty review;
- Responsive Beauty review;
- the Final Quality Test.

Automation, screenshots, pixel diffs, or rendered previews may support this review, but they may not supply the required human visual judgment.

## 3. Review-authority requirements

- Human optical: `human` or `combined`.
- Manual assistive technology: `human` or `combined`.
- Physical-device/native-platform: `combined`.
- Physical-device production performance: `combined`.
- Native Personalization adapter: `human` or `combined`.
- Namespace/equivalence cleanup: `combined`.

Automation may support a combined review but may not impersonate or replace the required human/physical component.

## 4. Real-evidence readiness audit

Audit the actual evidence directory against the frozen revision:

```sh
node scripts/evaluate_glaze_v1_3_qualification.mjs \
  --source-revision <PROMOTION_CANDIDATE_SHA>
```

During collection, a `blocked` result is expected and exits successfully so CI can report truthful partial readiness.

For the final qualification gate:

```sh
node scripts/evaluate_glaze_v1_3_qualification.mjs \
  --source-revision <PROMOTION_CANDIDATE_SHA> \
  --require-ready
```

`--require-ready` exits with status 2 unless all six tracks are accepted for that exact SHA. Even a successful result grants no lifecycle promotion.

## 5. Track 6 automated preparation

Run the source-namespace inventory:

```sh
python scripts/audit_glaze_v1_3_namespace.py --output /tmp/glaze-v1.3-namespace.json
```

The inventory is automated input only. Track 6 still requires a reviewed migration map, equivalence evidence, import-closure validation, and rollback verification before acceptance.

## 6. Promotion boundary

When all six records are accepted for one exact revision, readiness may become `ready-for-governed-candidate-promotion-review`. A separate governed change must then update lifecycle authority, Candidate entrypoints, and acceptance together. Until that decision is recorded, V1.3 remains Proposed and V1.2 remains Stable/current official.

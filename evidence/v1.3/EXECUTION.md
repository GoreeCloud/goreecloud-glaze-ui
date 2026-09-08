# GLAZE UI V1.3 Fresh Qualification Execution

**Status:** Qualification preparation / no workstream pass recorded  
**Release lifecycle:** Proposed  
**Qualification lifecycle:** Qualification active  
**Stable authority:** GLAZE UI V1.2 / `1.2.0`

This runbook controls fresh evidence collection for the staged GLAZE UI V1.3 release ladder. It does not activate Candidate, promote Stable, or grant consumer eligibility/conformance.

## 1. Freeze the Candidate-qualification source revision

Before the first five human/manual/physical/native reviews begin:

1. finish source-affecting implementation, visual-quality, qualification-tooling, lifecycle, and branch-reconciliation changes;
2. require green exact-head Phase 0, V1.2 Stable, Migration, Qualification Control Plane, Fresh Qualification, lifecycle-documentation, consumer-registry, and other applicable V1.3 CI;
3. select one exact lowercase 40-character Git SHA as the **Candidate-qualification source revision**;
4. record that SHA in the qualification tracking issue and in each of the first five evidence records;
5. do not silently retarget evidence after testing.

Evidence/reporting commits may be descendants of the tested source revision. Their records must continue to identify the exact source revision actually observed. A source change that can affect an observation invalidates affected evidence and requires a new qualification round.

## 2. Pre-Candidate qualification — five same-revision tracks

The Candidate gate is satisfied only when all five have current accepted evidence for the same exact Candidate-qualification SHA:

1. `human-optical-and-icon-collision-qualification`
2. `manual-assistive-technology-qualification`
3. `physical-device-native-platform-qualification`
4. `physical-device-production-performance-qualification`
5. `native-personalization-adapter-qualification`

Accepted records live directly in `evidence/v1.3/*.json` and conform to `contracts/v1.3/qualification-evidence.schema.json` using `schema_version: 2`.

A record contributes only when it is `passed`, explicitly accepted for the lifecycle gate, independently inspectable, unexpired, free of unresolved issues, and bound to the exact Candidate-qualification SHA.

### Human optical visual-quality boundary

The human optical pass must bind to `contracts/v1.3/quality-rules.candidate.json`, review all `quality-01` through `quality-55` exactly once, and explicitly accept the Visual Finish, Blandness Rejection, Accessibility-as-Beauty, Responsive Beauty, and Final Quality Test gates. Automation, screenshots, pixel diffs, or previews may support this review but may not supply the required human judgment.

## 3. Candidate readiness audit

During collection:

```sh
node scripts/evaluate_glaze_v1_3_qualification.mjs \
  --source-revision <CANDIDATE_QUALIFICATION_SHA>
```

For the final pre-Candidate gate:

```sh
node scripts/evaluate_glaze_v1_3_qualification.mjs \
  --source-revision <CANDIDATE_QUALIFICATION_SHA> \
  --require-ready
```

`--require-ready` exits with status 2 unless all five pre-Candidate tracks are accepted for that exact SHA. A successful result is only `ready-for-governed-candidate-promotion-review`; it grants no Candidate activation.

## 4. Governed Candidate promotion

Candidate activation is a separate exact-revision repository change. Lifecycle authority, Candidate entrypoints, and Candidate acceptance must be reviewed and recorded explicitly. Qualification evidence must not be rewritten to pretend it observed the later Candidate-activation commit.

Until the governed promotion occurs, V1.3 remains Proposed and V1.2 remains Stable/current official.

## 5. Post-Candidate Stable qualification — sixth track

Only after Candidate is active, prepare and execute:

`stable-activation-and-source-namespace-cleanup`

Freeze a later exact **Stable-promotion source revision**. This revision may differ from the Candidate-qualification SHA because Candidate activation and source cleanup are source changes.

The Stable cleanup record must preserve both identities:

- `environment.qualified_candidate_source_revision` = exact Candidate-qualification SHA;
- `environment.stable_promotion_source_revision` = exact Stable-promotion SHA;
- `environment.candidate_lifecycle_observed` = `active`;
- `environment.equivalence_review_completed` = `true`;
- `environment.import_closure_validated` = `true`;
- `environment.rollback_verified` = `true`.

Run the namespace inventory as automated input:

```sh
python scripts/audit_glaze_v1_3_namespace.py --output /tmp/glaze-v1.3-namespace.json
```

The inventory does not itself accept the Stable cleanup track.

## 6. Stable readiness audit

After Candidate activation and real Stable-cleanup review:

```sh
node scripts/evaluate_glaze_v1_3_stable_readiness.mjs \
  --candidate-source-revision <QUALIFIED_CANDIDATE_SHA> \
  --stable-source-revision <STABLE_PROMOTION_SHA> \
  --evidence-dir evidence/v1.3 \
  --candidate-active \
  --require-ready
```

A successful result is only `ready-for-governed-stable-promotion-review`. It does not update `VERSION`, lifecycle authority, Stable entrypoints, or consumer conformance.

## 7. Final lifecycle boundary

All six qualification requirements remain mandatory before Stable, but they are intentionally staged: five before Candidate on one exact SHA, and the sixth after Candidate on the exact later Stable-promotion SHA with explicit Candidate provenance. Stable requires a separate governed promotion decision after all applicable validation is green.

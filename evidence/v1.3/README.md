# GLAZE UI V1.3 Qualification Evidence

This directory is reserved for exact-revision qualification evidence produced for the active GLAZE UI V1.3 qualification workstream.

## Evidence boundary

V1.2 Stable evidence is historical input only. It may not be relabeled as a V1.3 pass.

Every accepted V1.3 qualification record must:

- target `GLAZE UI V1.3` / `1.3.0-candidate`;
- identify the exact 40-character source revision actually observed;
- use evidence `schema_version: 2` and conform to `contracts/v1.3/qualification-evidence.schema.json`;
- reference a governed workstream in `contracts/v1.3/qualification-matrix.json`;
- contain independently inspectable evidence references;
- distinguish human, automated, and combined review authority;
- remain fail-closed when evidence is missing, stale, superseded, mismatched, or unresolved.

A passed `human-optical-and-icon-collision-qualification` record has an additional mandatory boundary: it must reference `contracts/v1.3/quality-rules.candidate.json`, record all 55 governed quality rule IDs exactly once, and explicitly accept the visual-finish, blandness-rejection, accessibility-as-beauty, responsive-beauty, and final-quality-test gates. Automated validation, screenshots, or pixel comparison may support that review but cannot replace the required human authority.

A `passed` record is not equivalent to lifecycle promotion. Candidate and Stable promotion remain separate governed decisions.

## Staged exact-revision model

Qualification is deliberately split across lifecycle stages:

- **Pre-Candidate:** the first five workstreams in `contracts/v1.3/qualification-readiness.candidate.json` must all have accepted evidence for one identical exact Candidate-qualification source revision.
- **Post-Candidate / pre-Stable:** `stable-activation-and-source-namespace-cleanup` runs only after Candidate is active. It targets the later exact Stable-promotion source revision and must preserve provenance to the exact Candidate revision qualified by the first five records.
- **Before Stable:** all six requirements across both stages must be satisfied. The Stable gate is evaluated by `js/glaze-v1.3-stable-readiness.candidate.mjs` and remains non-promoting.

The Stable cleanup record therefore does **not** have to reuse the pre-Candidate source SHA. Requiring that would create a circular release ladder because Candidate activation and source-namespace cleanup are themselves governed source changes. Instead, Stable readiness requires explicit Candidate-revision provenance plus exact Stable-promotion-revision evidence.

Downstream consumer conformance and production acceptance remain separate from design-system qualification.

## Stable cleanup evidence semantics

A real passed `stable-activation-and-source-namespace-cleanup` record must use combined review authority and, in addition to the common evidence fields, record truthful environment facts consumed by the Stable readiness evaluator:

- `qualified_candidate_source_revision` — the exact SHA whose five-track Candidate qualification gate passed;
- `stable_promotion_source_revision` — the exact later SHA actually being reviewed for Stable promotion;
- `candidate_lifecycle_observed: "active"`;
- `equivalence_review_completed: true`;
- `import_closure_validated: true`;
- `rollback_verified: true`.

These values are not permission to promote. They are evidence inputs to a later governed Stable decision.

## Fail-closed qualification draft preparation

Use `scripts/prepare_glaze_v1_3_qualification_record.py` to initialize a session record without hand-authoring lifecycle-sensitive JSON. The helper supports all six qualification workstreams:

- `human-optical`
- `assistive-technology`
- `physical-device`
- `physical-performance`
- `personalization-adapter`
- `stable-activation`

Example:

```bash
python scripts/prepare_glaze_v1_3_qualification_record.py human-optical \
  --operator "Reviewer Name" \
  --output artifacts/v1.3/qualification-drafts/human-optical.json
```

The helper binds the draft to the checked-out immutable Git SHA by default. `--source-revision <40-character-sha>` may be used when the governed session intentionally targets another frozen revision. Optional `--platform` and `--device` labels are preparation hints only and must be verified during the real session.

The helper is deliberately unable to write into this `evidence/v1.3` directory. It only writes beneath `artifacts/v1.3/qualification-drafts/` and initializes every record as:

- `status: in_progress`;
- `disposition.accepted_for_lifecycle_gate: false`;
- an unresolved session-incomplete issue;
- a `DRAFT:` evidence-reference placeholder;
- no completed `quality_review` claim.

For human optical review, do not add a completed `quality_review` until a human reviewer has actually assessed all 55 governed rules and can truthfully record the required final visual-quality decisions. For manual assistive-technology and physical-device tracks, automation, simulation, emulation, screenshots, or synthetic results may support investigation but cannot substitute for the required real session.

After real qualification work is performed, create a separate immutable evidence record under `evidence/v1.3/`, replace all draft placeholders with independently inspectable references and truthful observations, validate it against the governed schema and the applicable Candidate or Stable readiness evaluator, and preserve the exact observed source revision. Do not overwrite a prior accepted record; supersession requires a new record.

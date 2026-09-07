# GLAZE UI V1.3 Qualification Evidence

This directory is reserved for exact-revision qualification evidence produced for the active GLAZE UI V1.3 qualification workstream.

## Evidence boundary

V1.2 Stable evidence is historical input only. It may not be relabeled as a V1.3 pass.

Every accepted V1.3 qualification record must:

- target `GLAZE UI V1.3` / `1.3.0-candidate`;
- identify the exact 40-character source revision observed;
- use evidence `schema_version: 2` and conform to `contracts/v1.3/qualification-evidence.schema.json`;
- reference the workstream in `contracts/v1.3/qualification-matrix.json`;
- contain evidence references that can be independently inspected;
- distinguish human, automated, and combined review authority;
- remain fail-closed when evidence is missing, stale, superseded, or unresolved.

A passed `human-optical-and-icon-collision-qualification` record has an additional mandatory boundary: it must reference `contracts/v1.3/quality-rules.candidate.json`, record all 55 governed quality rule IDs exactly once, and explicitly accept the visual-finish, blandness-rejection, accessibility-as-beauty, responsive-beauty, and final-quality-test gates. Automated validation, screenshots, or pixel comparison may support that review but cannot replace the required human authority.

A `passed` record is not equivalent to V1.3 lifecycle promotion. Promotion remains a separate governed decision after every blocking workstream has current accepted evidence for the exact promotion revision.

Downstream consumer conformance and production acceptance remain separate from design-system qualification.

## Fail-closed qualification draft preparation

Use `scripts/prepare_glaze_v1_3_qualification_record.py` to initialize a session record without hand-authoring lifecycle-sensitive JSON. The helper supports all six blocking workstreams:

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

The helper binds the draft to the checked-out immutable Git SHA by default. `--source-revision <40-character-sha>` may be used when the governed session is intentionally targeting another frozen revision. Optional `--platform` and `--device` labels are preparation hints only and must be verified during the real session.

The helper is deliberately unable to write into this `evidence/v1.3` directory. It only writes beneath `artifacts/v1.3/qualification-drafts/` and initializes every record as:

- `status: in_progress`;
- `disposition.accepted_for_lifecycle_gate: false`;
- an unresolved session-incomplete issue;
- a `DRAFT:` evidence-reference placeholder;
- no completed `quality_review` claim.

For human optical review, do not add a completed `quality_review` until a human reviewer has actually assessed all 55 governed rules and can truthfully record the required final visual-quality decisions. For manual assistive-technology and physical-device tracks, automation, simulation, emulation, screenshots, or synthetic results may support investigation but cannot substitute for the required real session.

After the real qualification work is performed, create a separate immutable evidence record under `evidence/v1.3/`, replace all draft placeholders with independently inspectable references and truthful observations, validate it against the governed schema and readiness evaluator, and preserve the exact observed source revision. Do not overwrite a prior accepted record; supersession requires a new record.

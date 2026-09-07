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

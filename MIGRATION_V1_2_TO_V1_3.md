# GLAZE UI V1.2 → V1.3 Migration and Consumer Boundary

**Status:** Proposed migration control plane  
**Current Stable authority:** GLAZE UI V1.2 / `1.2.0`  
**Current required consumer target:** GLAZE UI V1.2 / `1.2.0`  
**Planned V1.3 target:** GLAZE UI V1.3 — Adaptive Resonance / `1.3.0-candidate`  
**Lifecycle effect:** None  
**Production consumer migration enabled by this document:** No

This document defines how GoreeCloud consumers may evaluate and, only after a future lifecycle-eligible V1.3 release exists, migrate from GLAZE UI V1.2 to V1.3. It is a control plane and evidence contract. It does not activate V1.3 Candidate, Release Candidate, or Stable; it does not change `VERSION`; it does not change the live consumer target; and it does not migrate any consumer repository.

The machine-readable authority for this workstream is `contracts/v1.3/migration.candidate.json`. The adoption-record structure is defined by `contracts/v1.3/consumer-adoption-record.schema.json`.

## 1. Non-negotiable live boundary

Until a separate governed lifecycle action says otherwise:

- GLAZE UI V1.2 / `1.2.0` remains current Stable and current official.
- `consumers/registry.json.requiredConsumerVersion` remains `1.2.0`.
- V1.3 remains Proposed and non-consumer-eligible.
- No V1.3 Candidate release entrypoint is created by this workstream.
- No consumer may claim V1.3 production conformance from this repository's V1.3 development evidence.
- Existing V1.2 consumer obligations remain in force.

The `.candidate` suffix on an implementation artifact is source-stage naming, not lifecycle eligibility.

## 2. Evaluation before lifecycle eligibility

A consumer may use V1.3 Proposed or future Candidate references for explicit **non-production evaluation only**. Evaluation may include prototype integration, source review, local screenshots, component adaptation, accessibility testing, and migration planning.

Evaluation does not permit:

- changing the consumer's production Glaze target to V1.3;
- marking the consumer V1.3 conformant;
- treating a shared design-system CI pass as consumer evidence;
- treating imported tokens, copied styles, or a version-label edit as adoption;
- skipping repository-local accessibility, platform, product, performance, or production acceptance;
- claiming that a V1.3 presentation proves security, privacy, identity, sync, backup, or other underlying system truth.

The migration evaluator therefore returns `evaluation-only` whenever the evaluated release is not both Stable and consumer-eligible, even when a sample adoption record is otherwise complete.

## 3. Exact anchors are mandatory

Every migration record must bind two immutable source points:

1. **Consumer revision** — the exact 40-character commit SHA being accepted.
2. **Design-system revision** — the exact 40-character Glaze UI revision used by that consumer.

The record also names the design-system version. A later lifecycle-eligible release must match both the recorded version and recorded design-system revision used for the acceptance decision.

Branch names, moving tags, screenshots without source anchors, issue status, or "latest" references are insufficient evidence anchors.

## 4. Required consumer adoption record

A V1.3 consumer adoption record must include:

- consumer name;
- repository in `owner/name` form;
- exact consumer revision;
- design-system version;
- exact design-system revision;
- supported platform set;
- repository-local evidence categories;
- verified rollback information; and
- explicit production approval bound to the exact consumer revision.

The schema is intentionally fail-closed. Evidence may be `passed` or explicitly `not-applicable`; `missing`, `stale`, or `failed` evidence blocks production migration. A `not-applicable` result must still be recorded in the consumer repository and bound to the exact consumer revision so absence is not confused with acceptance.

## 5. Consumer evidence categories

The control plane requires the following categories, with platform-specific depth determined by the consumer:

### Rendered or native

Verify the actual supported implementation surface rather than source presence alone. Web-only evidence does not establish native parity; a native reference implementation does not establish a physical-device pass.

### Interaction

Verify keyboard, touch, pointer, focus, current/selected distinction, consequential-action confirmation, recovery behavior, and product-specific interaction paths as applicable.

### Accessibility

Verify applicable semantic structure, accessible names/roles/state, target floors, text scaling/reflow, Reduced Motion, Reduced Transparency, Forced Colors or platform equivalents, RTL, and assistive-technology behavior. Automated Glaze tests do not substitute for consumer-specific manual/AT acceptance where required.

### Responsive and form factor

Verify each supported environment or form factor represented by the consumer. Unsupported or unvalidated user-facing platforms remain production-blocked.

### Platform integration

Verify platform adapters and platform-owned behavior actually used by the consumer, including native appearance, system accessibility, input methods, windowing, wallpaper/personalization sources, or other integrations when applicable.

### Product workflows

Verify the consumer's own critical workflows and state truth. Glaze UI governs presentation and interaction but does not own product state.

### Performance

Verify the consumer's actual production performance boundary, including material degradation and motion behavior as applicable. Shared design-system micro-tests do not establish application performance.

### Production approval

A designated consumer-side authority must explicitly approve the exact consumer revision after required evidence is complete. The migration evaluator cannot manufacture this approval.

## 6. Readiness evaluator states

`js/glaze-v1.3-migration.candidate.mjs` is a pure, local policy evaluator. It performs no network access, persistence, lifecycle mutation, repository mutation, or deployment.

It may return:

- `evaluation-only` — the evaluated Glaze release is not Stable and consumer-eligible; no production migration can proceed.
- `blocked` — the release is lifecycle-eligible, but exact anchors, evidence, rollback, or record integrity are incomplete.
- `ready-for-consumer-acceptance` — technical evidence is complete for a lifecycle-eligible release, but explicit consumer production approval is still missing.
- `eligible-after-independent-acceptance` — the migration record satisfies this control plane, including explicit approval. This is a readiness result, **not a Glaze-generated conformance grant**; the consumer repository remains authoritative for its own acceptance claim.

The evaluator's `conformanceGranted` field is always `false` by design.

## 7. Production migration sequence after a future eligible release

Only after a separate governed V1.3 Stable promotion establishes a consumer-eligible release should a consumer execute this sequence:

1. Record the exact V1.3 Stable version and immutable design-system revision.
2. Record the consumer's current exact revision and last-known-good Glaze integration revision.
3. Create a repository-local migration change; do not rely on a centralized declaration.
4. Update the consumer to the eligible Stable entrypoint/contract according to that future release's instructions.
5. Revalidate applicable rendered/native, interaction, accessibility, responsive/form-factor, platform, product-workflow, and performance requirements.
6. Record every evidence category against the exact consumer revision.
7. Verify rollback on the consumer's own repository/integration path.
8. Obtain explicit production approval bound to that exact revision.
9. Update consumer-local conformance/adoption records only after those gates pass.
10. Update shared consumer registry state only through the separately governed registry process; this migration workstream does not do it automatically.

A consumer that fails any applicable gate remains on its previous verified integration.

## 8. Rollback

Rollback is consumer-local and must be prepared before production migration.

Each adoption record requires:

- an exact last-known-good consumer revision;
- confirmation that the rollback revision was verified;
- confirmation that the integration is independently reversible.

Rollback must restore the consumer to its recorded known-good integration. It must not rewrite Glaze release history, move immutable release tags, or pretend a failed consumer migration invalidates a correctly promoted design-system release.

A presentation-system upgrade is expected not to require product data migration, but each consumer must verify that assumption independently. If a product-specific migration introduces data/schema changes, that product owns its rollback/data-recovery plan.

## 9. Truth-domain ownership

Glaze UI owns presentation and interaction contracts. It does not become the authority for the state it displays.

For example:

- Privacy Shield remains authoritative for privacy state.
- Wardveil remains authoritative for security state.
- GoreeCloud Identity remains authoritative for identity/authentication state.
- Everkeep remains authoritative for backup/retention state.
- GoreeCloud Mesh and relevant networking services remain authoritative for their connectivity/state domains.
- Each product remains authoritative for its own records, workflow state, permissions, sync status, errors, and consequences.

A migration may change how truth is presented. It may not manufacture, strengthen, or silently reinterpret underlying truth.

## 10. Later rollout waves

The control plane records a future Stable rollout model but executes none of it now:

### Wave 1

Small, lower-risk consumers with clear rollback paths.

### Wave 2

Representative web, mobile, and desktop consumers after Wave 1 evidence is satisfactory.

### Wave 3

Remaining supported consumers after prior-wave evidence is satisfactory.

No wave is automatic. Evidence from one consumer or one wave cannot substitute for another consumer's repository-local evidence.

## 11. What this workstream does not establish

Phase 15 implementation/CI evidence does **not** establish:

- any consumer has migrated to V1.3;
- any consumer is V1.3 conformant;
- any consumer is V1.3 production-eligible;
- V1.3 lifecycle Candidate, RC, or Stable;
- native consumer parity;
- manual assistive-technology consumer acceptance;
- physical-device consumer acceptance;
- consumer production-performance acceptance; or
- cross-repository rollout execution.

Those remain later release-level or consumer-specific gates.

## 12. Validation

The repository validator and dedicated Phase 15 workflow verify that:

- V1.2 / `1.2.0` remains Stable/current official;
- the live consumer registry still requires `1.2.0` while V1.3 is Proposed;
- V1.3 remains Proposed and non-consumer-eligible;
- the migration contract, adoption-record schema, evaluator, tests, and guide agree;
- exact revision anchors are required;
- missing/stale/non-local evidence fails closed;
- rollback is required and independently reversible;
- production eligibility requires a future Stable consumer-eligible release plus explicit consumer approval;
- the evaluator cannot grant conformance or mutate lifecycle/consumer repositories; and
- no V1.3 Candidate release entrypoint is introduced by Phase 15.

## 13. Definition of done for Phase 15

Phase 15 is complete when the migration control plane, record schema, evaluator, tests, guide, validator, and CI are exact-head validated and the workstream is promoted to `implemented-and-validated` in the V1.3 development plan.

That completion unblocks **fresh V1.3 qualification planning**. It does not itself activate V1.3 Candidate or authorize consumer migration.

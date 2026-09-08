# GLAZE UI V1.2 → V1.3 Migration and Consumer Boundary

**Status:** Active Stable migration control plane  
**Previous Stable baseline:** GLAZE UI V1.2 / `1.2.0`  
**Current Stable authority:** GLAZE UI V1.3 — Adaptive Resonance / `1.3.0`  
**Current required consumer target:** GLAZE UI V1.3 / `1.3.0`  
**Consumer eligible:** Yes  
**Production consumer migration enabled:** Yes, after repository-local acceptance

This document defines how GoreeCloud consumers migrate from GLAZE UI V1.2 to the current Official Stable V1.3 release. The machine-readable consumer authority is `consumers/registry.json`; lifecycle authority is `registry/lifecycle.json` and `VERSION`.

V1.3.0 being consumer-eligible allows migration to begin. It does not automatically grant conformance or production approval to any downstream repository.

## 1. Current live boundary

- GLAZE UI V1.3 / `1.3.0` is current Official and current Stable.
- `consumers/registry.json.requiredConsumerVersion` is `1.3.0`.
- Stable web entrypoint: `css/glaze-v1.3.0.css`.
- Stable runtime entrypoint: `js/glaze-v1.3.0.mjs`.
- V1.2 remains a known-good historical rollback baseline.
- Consumers with only V1.2 evidence are migration-required for the current shared design-system target.
- Shared lifecycle authority does not manufacture downstream acceptance.

The `.candidate` suffix on inherited V1.3 implementation-source filenames records source-stage provenance. It does not change the Stable lifecycle of the `1.3.0` aggregate entrypoints.

## 2. Exact anchors are mandatory

Every migration record must bind:

1. the exact 40-character consumer revision being accepted;
2. the exact Glaze UI revision used by that consumer; and
3. design-system version `1.3.0`.

Branch names, moving tags, screenshots without source anchors, issue status, or generic `latest` references are insufficient evidence anchors.

## 3. Required consumer adoption record

A V1.3 consumer adoption record must include:

- consumer name and repository;
- exact consumer revision;
- design-system version and exact Glaze revision;
- supported platform set;
- repository-local evidence categories;
- verified rollback information; and
- explicit production approval bound to the exact consumer revision.

The existing machine schema remains `contracts/v1.3/consumer-adoption-record.schema.json`, with policy evaluation in `js/glaze-v1.3-migration.candidate.mjs`.

## 4. Consumer evidence categories

Each consumer must independently validate the applicable parts of its real product surface:

- **Rendered/native:** actual supported implementation surfaces, not source presence alone.
- **Interaction:** keyboard, touch, pointer, focus, selection/current-state distinction, consequential actions, and recovery behavior.
- **Accessibility:** names/roles/state, target floors, text scaling/reflow, Reduced Motion, Reduced Transparency, Forced Colors or platform equivalents, RTL, and applicable assistive-technology behavior.
- **Responsive/form factor:** each supported window, device, posture, or viewing environment.
- **Platform integration:** adapters and system-owned behavior actually used by the consumer.
- **Product workflows:** critical product-specific tasks and truthful state presentation.
- **Performance:** actual consumer performance and graceful degradation boundaries.
- **Production approval:** explicit consumer-side approval after required evidence is complete.

Shared Glaze automated validation does not replace repository-local manual/native/production acceptance where that acceptance is required.

## 5. Migration evaluator states

`js/glaze-v1.3-migration.candidate.mjs` remains a pure local policy evaluator. Its source filename is historical implementation provenance; it is part of the Stable V1.3 runtime through `js/glaze-v1.3.0.mjs`.

The evaluator may distinguish incomplete, technically ready, and independently accepted migration records. Its `conformanceGranted` behavior must remain fail-closed: Glaze itself does not grant downstream conformance.

## 6. Production migration sequence

1. Record the exact V1.3.0 Stable design-system revision used for migration.
2. Record the consumer's current exact revision and last-known-good V1.2 integration/revision.
3. Implement the repository-local migration using the V1.3 Stable entrypoints/contracts.
4. Revalidate applicable rendered/native, interaction, accessibility, responsive, platform, product-workflow, and performance requirements.
5. Record each evidence category against the exact consumer revision.
6. Verify rollback on the consumer's own integration path.
7. Obtain explicit production approval bound to that exact revision.
8. Update consumer-local adoption/conformance records only after those gates pass.
9. Update shared consumer registry state only through the governed registry process.

A consumer that fails any applicable gate remains non-conformant to the current shared target until corrected, even though V1.3.0 itself remains Stable.

## 7. Rollback

Rollback is consumer-local and must be prepared before production migration. It must restore a recorded known-good integration without rewriting Glaze release history or moving immutable release identities.

V1.2.0 remains available as the immediately preceding rollback baseline for the current reset-line V1.3 release.

## 8. Truth-domain ownership

Glaze UI owns presentation and interaction contracts, not underlying product truth. Privacy Shield remains privacy authority, Wardveil remains security authority, GoreeCloud Identity remains identity/authentication authority, Everkeep remains backup/retention authority, networking services remain connectivity authority, and each application remains authority for its own workflow state.

A migration may change how truth is presented. It may not manufacture, strengthen, or silently reinterpret underlying truth.

## 9. V1.3.1 follow-up relationship

The owner release decision moved unresolved human optical, manual assistive-technology, physical-device/native-platform, physical-device performance, native Personalization adapter, and source-namespace cleanup work into V1.3.1.

Those items are not represented as passed V1.3.0 evidence. Their existence does not revoke V1.3.0 Stable/consumer-eligible authority, and they do not remove any consumer's obligation to validate its own supported environment.

See `GLAZE_UI_V1_3_1_HARDENING.md` and `acceptance/v1.3-deferred-qualification.md`.

## 10. Migration definition of done

A consumer satisfies the current shared Glaze target only when its repository records exact V1.3.0 source anchors, applicable evidence, rollback, and explicit acceptance. The central `consumers/registry.json` may then record the consumer against `1.3.0` through the governed adoption process.

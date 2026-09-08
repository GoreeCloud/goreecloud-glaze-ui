# GLAZE UI V1.2 → V1.3 Migration and Consumer Boundary

**Status:** Active Stable migration control plane  
**Current Stable authority:** GLAZE UI V1.3 — Adaptive Resonance / `1.3.0`  
**Prior Stable baseline:** GLAZE UI V1.2 / `1.2.0`  
**Current required consumer target:** `1.3.0`  
**Production consumer migration enabled:** Yes, only after independent repository-local acceptance

This document defines how GoreeCloud consumers may migrate from GLAZE UI V1.2 to the current V1.3 Stable release. V1.3 Stable eligibility does not migrate or certify any consumer automatically.

The machine-readable adoption-record structure remains `contracts/v1.3/consumer-adoption-record.schema.json`, and the migration policy evaluator remains `js/glaze-v1.3-migration.candidate.mjs`. The `.candidate` source-stage filename does not change the current V1.3 Stable lifecycle authority.

## 1. Current lifecycle boundary

- GLAZE UI V1.3 / `1.3.0` is current Stable and current official.
- `consumers/registry.json.requiredConsumerVersion` is `1.3.0`.
- V1.3 is consumer-eligible but no consumer is auto-accepted.
- V1.2 remains the prior known-good Stable rollback baseline and historical migration source.
- The unresolved V1.3 qualification backlog is now V1.3.1 hardening work; it is not represented as V1.3.0 passing evidence.

## 2. Exact anchors are mandatory

Every consumer migration record must bind:

1. the exact 40-character consumer revision being accepted;
2. the exact 40-character Glaze UI revision used by that consumer; and
3. design-system version `1.3.0`.

Moving branch names, screenshots without source anchors, issue status, or a generic "latest" reference are insufficient acceptance anchors.

## 3. Required consumer evidence

A V1.3 consumer adoption must independently verify the categories applicable to that product and platform:

- rendered or native implementation behavior;
- interaction and state behavior;
- accessibility, semantics, input, reflow and applicable assistive-technology behavior;
- responsive/form-factor behavior;
- native/platform integration used by the consumer;
- product-specific workflows and truth-domain ownership;
- representative performance and graceful degradation;
- verified rollback; and
- explicit production approval bound to the exact consumer revision.

Evidence may be explicitly not applicable only when the consumer records a defensible scope reason against the exact revision. Missing, stale, failed, or unrelated evidence does not become acceptance.

## 4. Stable entrypoints

Consumers adopt V1.3 through the promoted Stable authorities appropriate to their implementation:

- `tokens/glaze-v1.3.json` for the Stable V1.3 token-family manifest;
- `js/glaze-v1.3.0.mjs` for the Stable runtime; and
- `css/glaze-v1.2.0.css` as the inherited validated web material/base layer where the web implementation uses that layer.

V1.3 did not introduce a monolithic versioned CSS implementation. Consumers must not fabricate or assume a nonexistent `css/glaze-v1.3.0.css` contract.

## 5. Migration sequence

1. Record the exact current consumer revision and last-known-good V1.2 integration revision.
2. Record the exact V1.3 Stable version and immutable Glaze UI revision being adopted.
3. Create a repository-local migration change.
4. Update token/runtime/contract references to the V1.3 Stable authorities actually used by the consumer.
5. Revalidate all applicable rendered/native, interaction, accessibility, responsive/form-factor, platform, product-workflow and performance requirements.
6. Record evidence against the exact consumer revision.
7. Verify rollback to the recorded known-good consumer integration.
8. Obtain explicit consumer-side production approval for that exact revision.
9. Update consumer-local conformance/adoption records only after applicable gates pass.
10. Update the shared consumer registry only through its governed process; the registry does not manufacture acceptance.

A consumer that fails an applicable gate remains on its previous verified integration.

## 6. V1.3.1 hardening interaction

`acceptance/v1.3.1-hardening.md` contains design-system qualification and cleanup work intentionally carried forward from the V1.3 promotion. Its existence does not revoke V1.3.0 Stable status, but consumers must still validate the platform/capability boundaries they actually claim.

If a consumer depends on a V1.3 capability whose applicable external/native evidence remains open, the consumer cannot use the design-system Stable label as a substitute for its own platform evidence.

## 7. Truth-domain ownership

Glaze UI owns presentation and interaction contracts. It does not become the authority for the state it displays. Privacy Shield remains authoritative for privacy state, Wardveil for security state, GoreeCloud Identity for identity/authentication state, Everkeep for backup/retention state, GoreeCloud Mesh and networking services for their connectivity domains, and each product for its own records, permissions, workflows and errors.

## 8. Rollback

Rollback is consumer-local and must be prepared before production migration. It must restore the recorded known-good integration without rewriting Glaze release history or moving immutable release references. Any consumer-specific data/schema migration remains that product's responsibility.

## 9. What V1.3 Stable does not establish

V1.3 Stable does not establish that any consumer has migrated, is conformant, is production-eligible, has native parity, has completed manual assistive-technology acceptance, has completed physical-device qualification, or has completed consumer production-performance acceptance. Those claims require consumer-local evidence.

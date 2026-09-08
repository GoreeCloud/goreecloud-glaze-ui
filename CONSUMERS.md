# GLAZE UI V1.3 Consumers

The machine-readable consumer registry authority for current consumer state is `consumers/registry.json`.

The required target for every applicable GoreeCloud user-facing consumer is **GLAZE UI V1.3 — Adaptive Resonance** (`1.3.0`). Fresh repository-local V1.3 adoption and acceptance evidence is required for each consumer; prior V1.2, V1.1, V1.0, Candidate, or pre-reset evidence does not automatically establish current conformance.

No consumer is production-eligible merely because GLAZE UI V1.3 is the current Stable platform target. Each application or service must independently satisfy its applicable rendered, interaction, accessibility, native/platform, product, performance, rollback, and release acceptance gates while preserving the authority of the system that owns the underlying state being presented.

## Registry status vocabulary

- `adoption-required` — the consumer has not yet supplied accepted current-Stable V1.3 evidence. `targetVersion`, `referenceRevision`, and `evidence` remain null.
- `unverified` — the current consumer state has not yet been verified against the V1.3 contract. Accepted target/revision/evidence fields remain null.
- `accepted-v1` — the consumer has completed governed product-specific acceptance for the current Stable `1.3.0` contract at an exact 40-character source revision with an evidence reference. This state still does not make the overall product production-eligible; product lifecycle/release authority remains independent.

The registry never carries an unresolved consumer as if it had accepted source evidence. An accepted consumer must target exactly the current Stable version and must identify the exact accepted source revision and evidence record.

## Migration boundary

V1.2 acceptance remains useful historical/migration evidence but cannot be relabeled as V1.3 acceptance. Consumers migrate independently using `MIGRATION_V1_2_TO_V1_3.md` and the exact-revision adoption record defined by `contracts/v1.3/consumer-adoption-record.schema.json`.

The V1.3.1 hardening workstream does not weaken consumer-specific acceptance. Consumers may only claim platforms and capabilities they independently validate, and open design-system hardening work must not be represented as completed consumer evidence.

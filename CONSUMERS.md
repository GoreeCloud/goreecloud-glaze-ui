# GLAZE UI V1.2 Consumers

The machine-readable consumer registry authority for current consumer state is `consumers/registry.json`.

The required target for every applicable GoreeCloud user-facing consumer is **GLAZE UI V1.2** (`1.2.0`). Fresh repository-local V1.2 adoption and acceptance evidence is required for each consumer; prior V1.1, V1.0, Candidate, or pre-reset evidence does not automatically establish current conformance.

No consumer is production-eligible merely because GLAZE UI V1.2 is the current Stable platform target. Each application or service must independently satisfy its applicable rendered, interaction, accessibility, native/platform, product, performance, and release acceptance gates while preserving the authority of the system that owns the underlying state being presented.

## Registry status vocabulary

- `adoption-required` — the consumer has not yet supplied accepted current-Stable V1.2 evidence. `targetVersion`, `referenceRevision`, and `evidence` remain null.
- `unverified` — the current consumer state has not yet been verified against the V1.2 contract. Accepted target/revision/evidence fields remain null.
- `accepted-v1` — the consumer has completed governed product-specific acceptance for the current Stable `1.2.0` contract at an exact 40-character source revision with an evidence reference. This state still does not make the overall product production-eligible; product lifecycle/release authority remains independent.

The registry never carries an unresolved consumer as if it had accepted source evidence. An accepted consumer must target exactly the current Stable version and must identify the exact accepted source revision and evidence record.

The V1.3 deferred qualification workstream does not weaken consumer-specific acceptance. Consumers may only claim the platforms and capabilities they independently validate.

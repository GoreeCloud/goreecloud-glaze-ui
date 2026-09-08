# GLAZE UI V1.3 Consumers

The machine-readable consumer registry authority for current consumer state is `consumers/registry.json`.

The required target for every applicable GoreeCloud user-facing consumer is **GLAZE UI V1.3 — Adaptive Resonance** (`1.3.0`). V1.3.0 is Official, Stable, and consumer-eligible on `main`. Fresh repository-local V1.3 adoption and acceptance evidence is required for each consumer; prior V1.2, V1.1, V1.0, Candidate, or pre-reset evidence does not automatically establish current conformance.

No consumer is production-eligible merely because GLAZE UI V1.3 is the current Stable platform target. Each application or service must independently satisfy its applicable rendered, interaction, accessibility, native/platform, product, performance, rollback, and release acceptance gates while preserving the authority of the system that owns the underlying state being presented.

## Stable consumer entrypoints

- Web: `css/glaze-v1.3.0.css`
- Runtime: `js/glaze-v1.3.0.mjs`
- Contract: `GLAZE_UI_V1_3.md`
- Migration guide: `MIGRATION_V1_2_TO_V1_3.md`

Historical `.candidate` filenames imported by the Stable runtime are preserved source-stage provenance. They do not make the current V1.3.0 release a Candidate.

## Registry status vocabulary

- `adoption-required` — the consumer has not yet supplied accepted current-Stable V1.3 evidence. It may retain historical target/evidence fields as migration provenance, but it does not satisfy the current required target.
- `unverified` — the current consumer state has not yet been verified against the V1.3 contract.
- `accepted-v1` — the consumer has completed governed product-specific acceptance for the current Stable contract at an exact 40-character source revision with an evidence reference. This state still does not make the overall product production-eligible; product lifecycle/release authority remains independent.

An accepted current consumer must target exactly the current Stable version and identify the exact accepted source revision and evidence record.

## V1.3.1 relationship

Unresolved human optical, manual assistive-technology, physical-device/native-platform, physical-device performance, native Personalization adapter, and source-namespace cleanup work has been moved to V1.3.1 by owner directive. Those items are not represented as passed V1.3.0 evidence.

The V1.3.1 carry-forward does not weaken consumer-specific acceptance. Consumers may only claim the platforms and capabilities they independently validate.

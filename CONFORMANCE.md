# GLAZE UI V1.3 Conformance

GLAZE UI V1.3 (`1.3.0`) is the current Stable Glaze UI conformance target. GLAZE UI V1.2 (`1.2.0`) remains the previous known-good Stable rollback baseline, not the current target.

The Glaze UI repository is authoritative for presentation, interaction, material, component, accessibility-contract, adaptive-layout, and design-system lifecycle state. It does not authenticate identities, authorize privacy operations, enforce security, prove recoverability, perform GoreeCloud Mesh coordination, or replace GoreeCloud Manager operational authority.

## Shared-system conformance

This repository's `goreecloud.platform.yaml` evaluates all seven GoreeCloud Integral Platform Systems. Integrations that do not belong inside the design-system source repository are explicitly recorded as `not-applicable-justified` rather than simulated. Those justifications do not waive any consuming application's own Manager, Privacy Shield, Wardveil Security, Everkeep, Glaze UI, Mesh, or Identity obligations.

GLAZE UI's own Platform System slot is `not-applicable-justified` because this repository implements that authority directly; a separate GLAZE-UI-to-GLAZE-UI runtime integration would be artificial.

## Consumer conformance

A consumer is conformant only when its exact repository revision satisfies the applicable V1.3 design, accessibility, interaction, responsive/form-factor, platform, semantic-state, migration/rollback, and production gates for that product.

Conformance must fail closed when required evidence is missing, stale, contradictory, or scoped to another revision. A consumer must not infer security, privacy, identity, continuity, operational, or integration truth from Glaze materials, colors, icons, motion, labels, or other presentation alone.

Promotion of the shared design system to V1.3 does not automatically make any downstream GoreeCloud application conformant. Each consumer must explicitly target `1.3.0` and produce its own exact-revision evidence for its supported platforms and production boundary.

## V1.3.1 boundary

The human optical/icon-artwork review, manual assistive-technology qualification, physical-device/native-platform qualification, physical-device production-performance qualification, native Personalization adapter qualification, and source-namespace/migration/rollback cleanup transferred from V1.3.0 into V1.3.1 remain unclaimed until real evidence exists.

That carry-forward does not invalidate the project-owner V1.3.0 Stable lifecycle decision, and it must not be rewritten as passed V1.3.0 evidence. Later V1.3.1 acceptance also does not retroactively certify downstream consumers; each consumer retains its own adoption and acceptance boundary.

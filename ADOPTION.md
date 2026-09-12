# GLAZE UI V1.3 Adoption

The current required Glaze UI adoption target is **GLAZE UI V1.3 — Adaptive Resonance** (`1.3.0`). GLAZE UI V1.2 (`1.2.0`) is the previous known-good Stable rollback baseline, not the current consumer target.

`consumers/registry.json` is the machine-readable consumer inventory. Its current baseline and required consumer version must remain synchronized with `VERSION`, `registry/lifecycle.json`, the Stable release record, and this guidance.

## Adoption requirements

Adoption is consumer-specific. A GoreeCloud consumer must explicitly target `1.3.0` and produce repository-local evidence for the exact revision being accepted. Importing tokens, copying styles, changing a version label, or loading the shared stylesheet does not establish conformance.

Applicable acceptance should cover the consumer's actual surface and risk boundary, including:

- source integration and deterministic dependency identity;
- rendered interaction and visual behavior;
- keyboard, touch, pointer, and assistive-input behavior as applicable;
- Reduced Motion, Reduced Transparency, Increased Contrast, Forced Colors, large text, and other supported accessibility preferences;
- responsive and supported form-factor behavior;
- semantic-state integrity so presentation never manufactures Manager, Privacy Shield, Wardveil Security, Everkeep, Mesh, Identity, or Sync truth;
- migration and rollback behavior;
- representative platform/device validation where the consumer claims native or device-specific support; and
- release, deployment, and production acceptance appropriate to that consumer.

## Fail-closed consumer state

A consumer remains `adoption-required` or otherwise unaccepted until its applicable V1.3 evidence is current and sufficient for the exact revision and supported-platform claim. Historical V1.2, legacy 2.x, or earlier Glaze acceptance remains historical evidence only and does not satisfy the current V1.3 target.

The shared V1.3.0 Stable promotion grants consumer eligibility, not downstream conformance. V1.3.1 qualification work also does not automatically change a consumer's state; consumers must deliberately adopt and validate any later approved release.

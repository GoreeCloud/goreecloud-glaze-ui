# GLAZE UI V1.0 — Historical Baseline Contract

**Official product identity at reset:** GLAZE UI V1.0  
**Machine version:** 1.0.0  
**Status:** Historical reset baseline; superseded as current authority by later governed releases  
**Current Stable successor:** GLAZE UI V1.2 / `1.2.0`  
**Repository:** `GoreeCloud/goreecloud-glaze-ui`

At the time of the V1.0 reset, GLAZE UI V1.0 became the sole current Glaze UI product version and the only version that could be named as the current GoreeCloud design-system target. This document preserves that reset-era contract as historical evidence; it does **not** define the current Stable or consumer-conformance target. Current authority is determined by `registry/lifecycle.json` and `VERSION`, which currently identify GLAZE UI V1.2 / `1.2.0` as Stable. V1.1 / `1.1.0` remains the prior Stable rollback and audit baseline.

## Design identity

GLAZE UI is GoreeCloud's shared visual and interaction design system. Its defining identity is ergonomic spatial hierarchy, Glaze Material, connected transformation, adaptive expression, accessibility-first interaction, and platform-aware behavior.

**Presentation rule:** Solid where users read or make explicit critical decisions. Glazed where users interact with transient navigation, command, search, control, or feedback chrome.

## V1.0 scope

The V1.0 baseline defines:

- Canvas → Surface → Soft Glaze → Glaze → Deep Glaze → Live Glaze material hierarchy.
- Light, Dark, and Deep Dark appearance modes.
- Calm, Balanced, and Expressive presentation profiles.
- Foundation, Structure, Overlay, Signature, and Intelligence component tiers.
- A 32-component canonical catalog.
- System Shell, Universal Search, Control Center, and workspace interaction patterns.
- Connected Transformation and adaptive density behavior.
- Reduced Motion, Reduced Transparency, Increased Contrast, Forced Colors, RTL, large-text, keyboard, pointer, touch, and assistive-input requirements.
- Minimum 48 px touch-oriented targets and 56 px Touch Assistance / far-view targets where applicable.
- Bounded Glaze use so readable content remains durable and interaction hierarchy remains clear.
- Platform-specific native mapping without replacing native platform semantics.

## Authority and verification

The V1.0 reset established the then-official product identity and contract namespace. It did not reuse earlier release identities as V1.0 evidence. Production-readiness, rendered-reference, native, accessibility, performance, and downstream consumer conformance required evidence against exact post-reset revisions.

No downstream application was upgraded by declaration. Each GoreeCloud application or service had to independently adopt V1.0 and satisfy its applicable acceptance requirements. The same evidence-first rule continues to apply to later Stable versions.

## Historical V1.0 entrypoints

- Version at V1.0 reset: `VERSION`
- V1.0 contract: `GLAZE_UI_V1_0.md`
- Lifecycle authority: `registry/lifecycle.json`
- Component catalog: `contracts/components/v1/catalog.json`
- System Shell contract: `contracts/system-shell/glaze-system-shell-v1.json`
- V1.0 web entrypoint: `css/glaze-v1.0.0.css`
- V1.0 runtime entrypoint: `js/glaze-v1.0.0.mjs`
- V1.0 acceptance boundary: `acceptance/v1.0-stable.md`
- V1 validator: `scripts/validate_glaze_v1.py`

Glaze Motion remained a separately governed experimental subsystem unless explicitly incorporated into a later governed GLAZE UI V1.x contract.

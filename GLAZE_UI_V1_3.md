# GLAZE UI V1.3 — Adaptive Resonance

**Lifecycle:** Official Stable  
**Machine version:** `1.3.0`  
**Current Stable authority:** GLAZE UI V1.3 / `1.3.0`  
**Baseline:** GLAZE UI V1.2 / `1.2.0` Stable  
**Release theme:** Adaptive Resonance  
**Created:** 2026-09-06  
**Official release decision:** 2026-09-08  
**Consumer eligible:** Yes  
**Branch authority:** `main`

GLAZE UI V1.3 — Adaptive Resonance is the current official Stable GoreeCloud design-system release. The V1.3 implementation was integrated on `main` before lifecycle activation; the owner subsequently issued a mandatory release directive establishing `1.3.0` as Official, Stable, and consumer-eligible and moving any remaining non-blocking qualification or cleanup issues to V1.3.1.

Lifecycle authority is recorded by `VERSION`, `registry/lifecycle.json`, `acceptance/v1.3-stable.md`, and the Stable entrypoints `css/glaze-v1.3.0.css` and `js/glaze-v1.3.0.mjs`.

## Governing direction

V1.3 extends the V1.2 material rule rather than replacing its safety boundary:

**Neutral glass remains the material foundation. Adaptive expression is contextual, bounded, and subordinate to meaning, accessibility, and task completion.**

The release combines three major directions:

1. **Adaptive Expression** — controlled dynamic color, expressive shape, typography response, personalization, and environmental/contextual adaptation.
2. **Human Ergonomics** — reachability, navigation placement, responsive composition, multi-pane behavior, foldable/posture adaptation, and human-centered interaction density.
3. **Living Material 2.0** — richer but bounded material response, depth, optical behavior, interaction feedback, and graceful degradation across platform and capability tiers.

## Implemented V1.3 workstreams

The integrated V1.3 implementation line contains validated source workstreams for:

- V1.3 contract and token architecture;
- adaptive/dynamic color and environmental accent behavior;
- expressive shape and component morphology;
- variable and responsive typography;
- Living Material 2.0 optical and interaction behavior;
- ergonomic reachability and adaptive navigation;
- responsive, multi-pane, large-screen, desktop, and foldable composition;
- Control Center and System Shell evolution;
- contextual intelligence and continuity behavior;
- motion, transition, and reduced-motion behavior;
- accessibility and resilience precedence;
- personalization controls and platform adapter boundaries;
- V1.3 signature-component/reference coverage; and
- migration and consumer-boundary controls.

The historical implementation plan remains at `contracts/v1.3/adaptive-resonance.plan.json`. Source artifacts may retain `.candidate` in their filenames as implementation-stage provenance; that suffix does not override the current Stable lifecycle authority.

## Stable entrypoints

Consumers target the release through:

- Web: `css/glaze-v1.3.0.css`
- Runtime: `js/glaze-v1.3.0.mjs`
- Reference: `reference/v1.3/signature-components-and-compositions.html`
- Migration: `MIGRATION_V1_2_TO_V1_3.md`

V1.3 inherits the verified V1.2 Stable rendering foundation and layers the integrated Adaptive Resonance runtime/contracts on top. V1.2 remains retained as a known-good rollback baseline.

## V1.3.1 follow-up boundary

The owner release decision explicitly moves unresolved work that previously blocked V1.3 lifecycle promotion into the V1.3.1 hardening and qualification track. These items are **not represented as passed V1.3.0 evidence**:

1. Human optical, visual-finish, and icon/artwork collision qualification, including the V1.3 quality-rule review set.
2. Manual assistive-technology qualification for the support matrix actually claimed.
3. Physical-device/native-platform qualification for claimed Android/OEM, Linux compositor/window, foldable/posture, and other platform behavior.
4. Physical-device production-performance qualification, including accepted budgets and representative real-device measurements.
5. Native Personalization persistence/system-appearance/wallpaper-source adapter qualification where claimed.
6. Stable activation/source-namespace cleanup, migration equivalence, import closure, and rollback hardening.

The follow-up authority is `GLAZE_UI_V1_3_1_HARDENING.md`. Historical V1.3 Candidate/deferred qualification records are retained as provenance but no longer block V1.3.0 Stable authority.

## Accessibility precedence

Accessibility and task completion outrank expressive treatment. Reduced Transparency, Reduced Motion, Increased Contrast, Forced Colors, RTL, large text/reflow, keyboard, pointer, touch, switch, voice, and assistive-technology semantics remain explicit engineering and consumer-acceptance dimensions.

Adaptive expression must never become the sole carrier of state, hierarchy, identity, progress, focus, error, success, warning, or interaction affordance.

## Performance and degradation

V1.3 may increase expressiveness only within bounded behavior. Material, motion, contextual response, dynamic color, and optical effects must degrade before correctness, legibility, focus, target size, semantic meaning, or task completion.

Representative physical-device production-performance requalification remains V1.3.1 follow-up and is not claimed as completed V1.3.0 evidence.

## Consumer boundary

V1.3.0 is consumer-eligible and is the current shared design-system target. Consumer eligibility does **not** automatically make a downstream GoreeCloud product conformant, accepted, or production-ready.

Each consumer must perform repository-local migration and acceptance appropriate to its supported platforms and product truth domains. A consumer must not claim V1.3 conformance merely because V1.3.0 is Stable, because shared Glaze CI passes, or because it imports a Stable entrypoint. Consumer-local accessibility, platform, workflow, rollback, performance, and production approval remain independent obligations.

The shared required target is recorded in `consumers/registry.json`.

## Evidence integrity

The owner lifecycle decision changes which unresolved items block V1.3.0 release. It does not rewrite unfinished evidence into successful evidence. Automated validation remains automated validation; human/manual/physical-device evidence remains unclaimed unless actually performed and recorded.

This distinction is mandatory for auditability and continues into V1.3.1.

## Naming boundary

The full release-theme name is **GLAZE UI V1.3 — Adaptive Resonance**.

Within GoreeCloud cross-product records, do not shorten the release theme to standalone **Resonance**, because that name is already used by the GoreeCloud Music capability identity.

## Release definition of done

V1.3.0 is released when the authoritative `main` state contains:

- `VERSION` = `1.3.0`;
- `registry/lifecycle.json.currentOfficial` = `1.3.0`;
- `registry/lifecycle.json.currentStable` = `1.3.0`;
- a consumer-eligible V1.3 release record;
- `consumers/registry.json.requiredConsumerVersion` = `1.3.0`;
- Stable web/runtime entrypoints;
- an explicit Stable acceptance record; and
- the unresolved qualification/cleanup backlog assigned to V1.3.1 without fabricated pass claims.

Those conditions establish release authority. Downstream consumer acceptance remains separate.

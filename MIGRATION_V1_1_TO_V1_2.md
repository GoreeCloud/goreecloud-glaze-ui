# GLAZE UI V1.1 → V1.2 Implementation and Migration Plan

**Status:** Candidate implementation plan  
**Stable authority:** GLAZE UI V1.1 / `1.1.0`  
**Target under development:** GLAZE UI V1.2 / `1.2.0-candidate`  
**Production migration target:** None until governed V1.2 Stable promotion  
**Baseline inspected:** `0a3baf4f0413b4ca6009656772df2467059caae3` on `main`

This plan translates the proposed **Frosted Optical Material Update** into repository changes, machine-readable contracts, implementation work, validation, acceptance gates, and a controlled migration path. It does not promote V1.2, alter the current Stable version, or establish downstream consumer conformance.

## 1. Non-negotiable migration boundary

V1.1 remains the known-good Stable baseline while V1.2 is developed.

During Candidate development:

- `VERSION` remains `1.1.0`.
- `registry/lifecycle.json.currentStable` remains `1.1.0`.
- V1.2 remains `consumerEligible: false`.
- V1.1 CSS and runtime entrypoints remain present and validated.
- Candidate presentation remains explicit opt-in.
- No downstream application may claim V1.2 production conformance.
- Semantic color, truthful system state, accessibility, resilience, platform adaptation, and the inherited material budget remain controlling requirements.

## 2. Current repository reality

The repository already contains a substantial V1.2 Candidate implementation. This plan starts from that evidence instead of recreating it.

| Area | Current state at inspected baseline | Plan treatment |
| --- | --- | --- |
| Neutral frosted substrate | Implemented Candidate | Preserve and align to Frosted Optical roles |
| 32-component material map | Implemented Candidate | Keep exact catalog parity; refine optical roles |
| Five-region System Shell map | Implemented Candidate | Keep inherited region and material-budget parity |
| Web reference/rendered evidence | Bounded Candidate evidence | Extend to explicit Frost White/Ice Blue acceptance |
| Android native reference | Bounded Candidate evidence | Revalidate when optical foundation changes |
| Linux GTK reference | Bounded Candidate evidence | Revalidate when optical foundation changes |
| Frost White/Ice Blue named optical foundation | Not fully contracted at baseline | Contract in this tranche |
| Clear/Mist/Frost/Dense Frost/Opaque Frost | Not fully contracted at baseline | Contract in this tranche |
| Frost/Ice/Crystal/Content Aura system | Not fully contracted at baseline | Contract in this tranche |
| Full/Reduced/Minimal performance profiles | Not fully contracted at baseline | Contract in this tranche |
| Controlled V1.1 → V1.2 migration gates | Missing at baseline | Contract and validate in this tranche |
| Downstream consumer migration evidence | Not started | Begins only after governed Stable promotion |

## 3. Target optical architecture

V1.2 is not a white-and-blue theme. Its defining rules are:

> **The material is the identity.**

- White behaves as light.
- Blue behaves as atmosphere.
- Translucency behaves as depth.
- Durable reading and consequential surfaces remain solid or near-solid when needed.
- Frost, blur, edge illumination, luminance, opacity, and shadow establish depth before hue.

The candidate optical identity is machine-readable in `tokens/glaze-v1.2-optical-foundation.candidate.json`.

### Primary optical references

- Frost White — `#F4F8FA`
- Crystal White — `#FBFDFE`
- Ice Blue — `#DCECF6`
- Glacier Blue — `#8FC4E8`
- Clear Sky Blue — `#68AEE0`
- Cloud Gray — `#DCE3E8`
- Slate Gray — `#7E8D99`
- Cool Graphite — `#151C22`
- Deep Graphite — `#0E1419`
- Blue-Black — `#070C11`

These are optical references, not replacements for protected semantic color roles.

### Frost levels

V1.2 contracts five independent frost intents:

1. **Clear** — minimal diffusion.
2. **Mist** — light visual softening.
3. **Frost** — standard Glaze treatment.
4. **Dense Frost** — greater environmental abstraction.
5. **Opaque Frost** — near-solid accessibility/performance fallback.

Opacity and frost are independent controls; a surface must not infer one from the other.

### Visual distribution target

Representative interfaces should normally remain within these broad optical proportions:

- 65–80% neutral canvas/surface/white/gray/graphite.
- 15–25% frosted translucent material.
- 3–10% Ice Blue atmospheric influence.
- Minimal stronger accent color.

This is an acceptance heuristic, not a pixel quota.

## 4. Repository change architecture

### 4.1 Foundation contracts and tokens

Candidate authority is split intentionally:

- `tokens/glaze-v1.2-frosted-neutral.candidate.json` — existing substrate and inherited material behavior.
- `tokens/glaze-v1.2-optical-foundation.candidate.json` — new Frost White/Ice Blue identity, frost taxonomy, Aura families, distribution, performance profiles, and anti-patterns.
- `contracts/v1.2/component-materials.candidate.json` — exact 32-component material mapping.
- `contracts/v1.2/system-shell-materials.candidate.json` — exact five-region System Shell mapping.
- `contracts/v1.2/migration.candidate.json` — migration lifecycle, stages, gates, rollback, and consumer rollout rules.

The optical foundation initially **extends** the existing Frosted Neutral layer. Before RC, legacy V1.1 teal/amber Aura compatibility fields must be retired or explicitly mapped to Frost/Ice behavior.

### 4.2 Web implementation

Existing Candidate layers remain the working implementation:

- `css/glaze-v1.2-frosted-neutral.candidate.css`
- `css/glaze-v1.2-components.candidate.css`
- `css/glaze-v1.2-system-shell.candidate.css`
- `css/glaze-v1.2-accessibility.candidate.css`
- `css/glaze-v1.2.0-candidate.css`

Next implementation work must consume named optical roles rather than scattering literal Frost White/Ice Blue values through component CSS.

### 4.3 Component work

The current exact 32-component mapping is retained. V1.2 refinement proceeds by role, not by making every component translucent.

Priority order:

1. `GlzUniversalSearch` — signature V1.2 showcase.
2. Floating navigation, Smart Rail, Dock, Toolbar, Capsule.
3. Popover, Menu, Tooltip, Sheet, Toast.
4. Foundation controls with explicit Glaze variants.
5. Durable cards/lists/tables and intelligence content surfaces — preserve reading-first treatment.
6. Dialog and critical-system surfaces — preserve consequential-decision clarity.

Each component must define applicable default, hover, focus, pressed, selected, disabled, loading, semantic, offline/unavailable, protected/restricted, Reduced Transparency, Increased Contrast, Forced Colors, and performance-degraded behavior.

### 4.4 Appearance work

Reference acceptance must explicitly cover:

- **Light:** Cloud Gray/soft-white canvas, Frost White translucent chrome, restrained Ice Blue reflection, cool graphite text.
- **Dark:** cool graphite canvas, charcoal surfaces, smoky Glaze, cool-white edges, restrained Ice Blue.
- **Deep Dark:** Blue-Black canvas → cool graphite surface → charcoal translucent Glaze → Frost White edge → faint Ice Blue reflection.

## 5. Performance and accessibility profiles

### Full

May use controlled blur, environmental tint, Aura, adaptive opacity, and connected material transitions.

### Reduced

Uses lower blur, simpler shadows, static tint, reduced Aura, and bounded transitions.

### Minimal

Uses near-solid surfaces, no blur, basic edge treatment, no Aura, and preserves hierarchy.

Accessibility behavior always overrides decorative fidelity. Reduced Transparency must look intentionally designed rather than visually broken; Forced Colors remains platform-authoritative; Reduced Motion removes nonessential travel and dynamic optical motion without changing semantic state.

## 6. Implementation stages and blocking gates

The machine-readable sequence lives in `contracts/v1.2/migration.candidate.json`.

### M0 → G0 — Stable Baseline Integrity

Pass only when V1.1 remains intact, V1.2 remains non-consumer-eligible, and current Stable authority has not moved.

### M1 → G1 — Optical Foundation Contract

Pass when the Frost White/Ice Blue palette, frost levels, Aura families, visual distribution, performance profiles, and anti-patterns are machine-readable and validated.

### M2 → G2 — Component and System Shell Contract Parity

Pass when all 32 components and all five System Shell regions retain exact inherited coverage and material budgets, with reading/decision surfaces protected.

### M3 → G3 — Rendered Optical Acceptance

Pass when actual Candidate implementation consumes the optical foundation and source-pinned Light, Dark, and Deep Dark evidence demonstrates the intended Frosted Optical identity. Legacy teal/amber Aura compatibility must be retired or mapped before this gate can lead to RC.

### M4 → G4 — Accessibility, Performance, and Resilience

Pass when Reduced Transparency, Increased Contrast, Forced Colors, Reduced Motion, 200%+ text, RTL, applicable assistive technology behavior, and Full/Reduced/Minimal profiles preserve hierarchy, readability, semantics, and interaction.

### M5 → G5 — RC Exact-Head Acceptance

Pass only for one exact candidate revision after required CI, supported-platform evidence, human optical review, documentation, known-defect review, and rollback verification.

### M6 → G6 — Stable Release Promotion

This is a separate governed release action. `VERSION`, lifecycle authority, immutable release/tag identity, and Stable acceptance must move together. A merge alone does not satisfy G6.

### M7 → G7 — Consumer Migration Acceptance

Occurs per consumer after Stable promotion. Every consumer must produce fresh repository-local evidence. Design-system evidence cannot substitute for consumer evidence.

## 7. Consumer rollout strategy

### Candidate period

- Design-system repository and explicit non-production opt-in only.
- No production conformance claims.
- Consumers may use Candidate references for evaluation, not as Stable authority.

### RC period

- Bounded pilot evaluation only after G5.
- Exact RC revision required.
- Pilot evidence cannot establish broad production support.

### Stable Wave 1

- Small, lower-risk consumer set with simple rollback.
- Require exact design-system anchor and fresh consumer acceptance.

### Stable Wave 2

- Representative web, mobile, and desktop consumers after Wave 1 evidence is satisfactory.

### Stable Wave 3

- Remaining supported consumers, prioritized by dependency/complexity/risk.

No wave is automatic. A consumer remains on its last verified Stable Glaze UI integration until its own migration is complete and accepted.

## 8. Rollback design

Before V1.2 Stable, rollback is simple: remove Candidate opt-in and continue consuming V1.1 Stable entrypoints.

After V1.2 Stable, each consumer must record its own last-known-good integration revision. A failed V1.2 migration rolls back the consumer to that verified revision; it does not rewrite design-system history or move an immutable Stable tag.

No data migration is expected from a presentation-system upgrade, but product-specific migrations must verify that assumption independently.

## 9. Validation

`python scripts/validate_glaze_v1_2_migration.py` is a fail-closed control-plane validator. It verifies at minimum:

- V1.1 Stable authority has not moved.
- V1.2 remains Candidate and non-consumer-eligible.
- lifecycle registry binds the optical foundation, migration contract, and promotion-gate record.
- the exact proposed optical palette is present.
- all five frost levels are present.
- Frost/Ice/Crystal/Content Aura families are present.
- Full/Reduced/Minimal performance profiles are present.
- teal/purple are prohibited as default V1.2 atmosphere.
- migration stages and gates remain complete and ordered.
- CI continues to execute the migration validator.

This validator supplements, rather than replaces, rendered, accessibility, runtime, native, performance, and human optical review.

## 10. Promotion checklist

V1.2 must not be promoted Stable until all applicable items are verified on the exact candidate revision:

- [ ] Candidate contract and token set complete.
- [ ] Frost White/Ice Blue optical implementation complete.
- [ ] Legacy V1.1 atmosphere compatibility retired or governed.
- [ ] 32-component contract and implementation coverage complete.
- [ ] System Shell contract and implementation coverage complete.
- [ ] Light, Dark, and Deep Dark reference scenes accepted.
- [ ] Universal Search signature treatment accepted.
- [ ] Reduced Transparency accepted as a polished mode.
- [ ] Increased Contrast and Forced Colors accepted.
- [ ] Reduced Motion and connected transformations accepted.
- [ ] 200%+ text and RTL validated where applicable.
- [ ] Full/Reduced/Minimal performance profiles validated.
- [ ] Supported platform/form-factor evidence current and source-pinned.
- [ ] Visual regression suite current.
- [ ] Human optical review completed on exact head.
- [ ] Known release-blocking defects resolved.
- [ ] Migration and rollback documentation current.
- [ ] All required CI checks pass on exact head.
- [ ] Stable lifecycle promotion separately approved and recorded.

## 11. Definition of done

The V1.2 migration program is complete only when:

1. V1.2 has been implemented and validated against its current authoritative contracts.
2. the exact release revision has passed all required acceptance gates;
3. V1.2 has been separately promoted to Stable through governed release procedures;
4. consumer migration has proceeded through controlled waves; and
5. each migrated consumer has fresh exact-revision conformance and production-acceptance evidence.

Until then, V1.1 / `1.1.0` remains the production consumer target.

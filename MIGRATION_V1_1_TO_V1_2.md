# GLAZE UI V1.1 → V1.2 Implementation and Migration Plan — Historical Closure

**Status:** Historical Candidate implementation plan; closed by governed V1.2 Stable promotion on 2026-09-06  
**Stable authority during Candidate execution:** GLAZE UI V1.1 / `1.1.0`  
**Historical target under development:** GLAZE UI V1.2 / `1.2.0-candidate`  
**Current Stable authority:** GLAZE UI V1.2 / `1.2.0`  
**Current production migration target:** GLAZE UI V1.2 / `1.2.0`, subject to independent consumer acceptance  
**Baseline inspected:** `0a3baf4f0413b4ca6009656772df2467059caae3` on `main`

This plan translated the proposed **Frosted Optical Material Update** into repository changes, machine-readable contracts, implementation work, validation, acceptance gates, and a controlled migration path. It is retained as a historical Candidate-era execution record and does not override current V1.2 Stable lifecycle authority.

On 2026-09-06, the GoreeCloud project owner explicitly promoted GLAZE UI V1.2 to Stable and moved the remaining human optical, manual assistive-technology, physical-device/OEM/compositor, production-performance, applicable native Personalization-adapter, and compatibility-namespace qualification work to V1.3. Historical unchecked Candidate checklist items below therefore remain historical/deferred; they are **not** retroactively represented as passed V1.2 evidence. Downstream consumer conformance remains independent and fail-closed.

## 1. Historical non-negotiable migration boundary

V1.1 remained the known-good Stable baseline while V1.2 was developed.

During Candidate development:

- `VERSION` remained `1.1.0`.
- `registry/lifecycle.json.currentStable` remained `1.1.0`.
- V1.2 remained `consumerEligible: false`.
- V1.1 CSS and runtime entrypoints remained present and validated.
- Candidate presentation remained explicit opt-in.
- No downstream application could claim V1.2 production conformance.
- Semantic color, truthful system state, accessibility, resilience, platform adaptation, and the inherited material budget remained controlling requirements.

Those constraints describe the historical Candidate phase. Live lifecycle authority now resides in V1.2 Stable / `1.2.0`, while V1.1 remains the previous known-good rollback release.

## 2. Repository reality at the inspected Candidate baseline

The repository already contained a substantial V1.2 Candidate implementation. This plan started from that evidence instead of recreating it.

| Area | State at inspected baseline | Plan treatment |
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

The promoted-source optical identity remains machine-readable in `tokens/glaze-v1.2-optical-foundation.candidate.json`; the Candidate suffix is retained as source lineage and does not describe the live V1.2 lifecycle.

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

Candidate-era source authority was split intentionally:

- `tokens/glaze-v1.2-frosted-neutral.candidate.json` — substrate and inherited material behavior.
- `tokens/glaze-v1.2-optical-foundation.candidate.json` — Frost White/Ice Blue identity, frost taxonomy, Aura families, distribution, performance profiles, and anti-patterns.
- `contracts/v1.2/component-materials.candidate.json` — exact 32-component material mapping.
- `contracts/v1.2/system-shell-materials.candidate.json` — exact five-region System Shell mapping.
- `contracts/v1.2/migration.candidate.json` — historical migration lifecycle, stages, gates, rollback, and consumer rollout rules.

These Candidate-suffixed files remain frozen promoted-source lineage under the Stable V1.2 wrapper/registry authority. The optical foundation continues to extend the Frosted Neutral substrate, but V1.2 no longer exposes teal/amber Aura alpha tokens. Frost/Ice/Crystal/Content is the V1.2 Aura authority. Inherited V1.1 `--glz11-aura-teal-max` and `--glz11-aura-amber-max` CSS variables remain only as `transparent` compatibility neutralizers in the V1.2 compatibility layers until a future Stable source set can remove the inherited declarations; they are not V1.2 atmospheric values.

### 4.2 Web implementation

The promoted implementation retains the Candidate-era source layers:

- `css/glaze-v1.2-frosted-neutral.candidate.css`
- `css/glaze-v1.2-components.candidate.css`
- `css/glaze-v1.2-system-shell.candidate.css`
- `css/glaze-v1.2-accessibility.candidate.css`
- `css/glaze-v1.2.0-candidate.css` as historical preview composition
- `css/glaze-v1.2.0.css` as the current Stable web entrypoint

Stable consumers use the governed V1.2 Stable entrypoint. Candidate-era naming cleanup is deferred to V1.3 rather than changing V1.2 pixels during promotion.

### 4.3 Component work

The exact 32-component mapping is retained. V1.2 refinement proceeds by role, not by making every component translucent.

Priority order:

1. `GlzUniversalSearch` — signature V1.2 showcase.
2. Floating navigation, Smart Rail, Dock, Toolbar, Capsule.
3. Popover, Menu, Tooltip, Sheet, Toast.
4. Foundation controls with explicit Glaze variants.
5. Durable cards/lists/tables and intelligence content surfaces — preserve reading-first treatment.
6. Dialog and critical-system surfaces — preserve consequential-decision clarity.

Each component defines applicable default, hover, focus, pressed, selected, disabled, loading, semantic, offline/unavailable, protected/restricted, Reduced Transparency, Increased Contrast, Forced Colors, and performance-degraded behavior.

### 4.4 Appearance work

Reference acceptance covers:

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

## 6. Historical implementation stages and blocking gates

The Candidate-era machine-readable sequence remains in `contracts/v1.2/migration.candidate.json` for provenance.

### M0 → G0 — Stable Baseline Integrity

Historical Candidate condition: V1.1 intact, V1.2 non-consumer-eligible, and current Stable authority not moved during Candidate development.

### M1 → G1 — Optical Foundation Contract

Frost White/Ice Blue palette, frost levels, Aura families, visual distribution, performance profiles, and anti-patterns machine-readable and validated.

### M2 → G2 — Component and System Shell Contract Parity

All 32 components and all five System Shell regions retain exact inherited coverage and material budgets, with reading/decision surfaces protected.

### M3 → G3 — Rendered Optical Acceptance

Candidate implementation consumes the optical foundation and source-pinned Light, Dark, and Deep Dark evidence demonstrates the intended Frosted Optical identity. The V1.2 token-level legacy teal/amber Aura compatibility requirement is satisfied; bounded inherited V1.1 Aura variables remain transparent-only compatibility neutralizers and may not carry chromatic values.

### M4 → G4 — Accessibility, Performance, and Resilience

Candidate-era gate covered Reduced Transparency, Increased Contrast, Forced Colors, Reduced Motion, 200%+ text, RTL, applicable assistive technology behavior, and Full/Reduced/Minimal profiles. Any portions not actually completed before the owner-approved release-scope change remain deferred rather than retroactively passed.

### M5 → G5 — RC Exact-Head Acceptance

Historical Candidate/RC gate record. Human/manual/physical items not completed before the 2026-09-06 owner decision are carried to V1.3.

### M6 → G6 — Stable Release Promotion

Completed as a separate governed release action on 2026-09-06. `VERSION`, lifecycle authority, Stable wrappers, acceptance records, and current target moved to V1.2 / `1.2.0`. This does not imply that every earlier Candidate checklist item passed.

### M7 → G7 — Consumer Migration Acceptance

Remains per consumer after Stable promotion. Every consumer must produce fresh repository-local evidence. Design-system evidence cannot substitute for consumer evidence.

## 7. Consumer rollout strategy

### Historical Candidate period

- Design-system repository and explicit non-production opt-in only.
- No production conformance claims.
- Consumers could use Candidate references for evaluation, not as Stable authority.

### Historical RC period

- Bounded pilot evaluation only after applicable RC gates.
- Exact RC revision required.
- Pilot evidence could not establish broad production support.

### Stable Wave 1

- Small, lower-risk consumer set with simple rollback.
- Require exact design-system anchor and fresh consumer acceptance.

### Stable Wave 2

- Representative web, mobile, and desktop consumers after Wave 1 evidence is satisfactory.

### Stable Wave 3

- Remaining supported consumers, prioritized by dependency/complexity/risk.

No wave is automatic. A consumer remains on its last verified Glaze UI integration until its own V1.2 migration is complete and accepted.

## 8. Rollback design

During Candidate development, rollback was simple: remove Candidate opt-in and continue consuming V1.1 Stable entrypoints.

After V1.2 Stable, each consumer records its own last-known-good integration revision. A failed V1.2 migration rolls back the consumer to that verified revision; it does not rewrite design-system history or move an immutable Stable tag. V1.1 / `1.1.0` remains the previous known-good design-system rollback release.

No data migration is expected from a presentation-system upgrade, but product-specific migrations must verify that assumption independently.

## 9. Validation after Stable promotion

`python scripts/validate_glaze_v1_2_migration.py` now validates the frozen Candidate-era migration control plane as historical promoted-source evidence **after** requiring the live V1.2 Stable lifecycle. It does not replace `scripts/validate_glaze_v1.py` or the Stable acceptance authority.

The compatibility validation verifies at minimum that:

- the live repository remains V1.2 Stable / `1.2.0`;
- the preserved historical migration source remains internally coherent against its V1.1 Stable baseline and V1.2 Candidate development identity;
- the exact proposed optical palette remains present;
- all five frost levels remain present;
- Frost/Ice/Crystal/Content Aura families remain present;
- Full/Reduced/Minimal performance profiles remain present;
- teal/purple remain prohibited as default V1.2 atmosphere;
- V1.2 Frosted Neutral atmosphere no longer contains legacy teal/amber Aura alpha maps;
- any inherited V1.1 teal/amber Aura variable assignment in a V1.2 promoted-source CSS layer is `transparent` only;
- historical migration stages and gates remain complete and ordered; and
- historical source validation does not manufacture current release or downstream acceptance evidence.

These validators supplement, rather than replace, rendered, accessibility, runtime, native, performance, and human optical review. Deferred V1.3 qualifications remain deferred.

## 10. Historical promotion checklist snapshot

The following list is preserved as the Candidate-era plan snapshot. Unchecked items are **not** converted to completed evidence by the Stable promotion; where still relevant, they are carried forward to V1.3 or consumer-specific adoption work.

- [ ] Candidate contract and token set complete.
- [ ] Frost White/Ice Blue optical implementation complete.
- [x] Legacy V1.1 atmosphere compatibility retired or governed.
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
- [x] Stable lifecycle promotion separately approved and recorded on 2026-09-06.

**Owner-approved closure:** Remaining release blockers and external/manual/physical qualification items were postponed to GLAZE UI V1.3. The historical unchecked state above remains truthful evidence of the Candidate plan at closure.

## 11. Current definition of done and continuing boundary

The shared design-system V1.2 release is now Stable under the owner-approved 2026-09-06 lifecycle decision and current repository authority. The old Candidate migration program is closed as a historical plan.

Completion of the shared V1.2 release does **not** mean:

1. every historical Candidate checklist item passed;
2. deferred V1.3 human/manual/physical qualification was performed;
3. every GoreeCloud consumer migrated; or
4. downstream production acceptance was granted automatically.

Current consumers target GLAZE UI V1.2 / `1.2.0` and must produce fresh exact-revision conformance and production-acceptance evidence independently. V1.1 / `1.1.0` remains the previous known-good rollback baseline.

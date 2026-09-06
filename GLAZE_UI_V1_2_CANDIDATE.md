# GLAZE UI V1.2 — Frosted Neutral Material Candidate — Historical Promoted-Source Contract

**Lifecycle:** Historical Candidate source contract; superseded as current lifecycle authority  
**Stable baseline during Candidate development:** GLAZE UI V1.1 / 1.1.0  
**Promotion status:** Promoted into GLAZE UI V1.2 Stable / 1.2.0 on 2026-09-06; Candidate-suffixed source paths are retained as frozen promoted-source lineage  
**Current Stable contract:** `GLAZE_UI_V1_2.md`  
**Primary intent:** Move the default Glaze material from teal/amber atmospheric tinting toward frosty, white, blurred, translucent neutral glass.

This document preserves the V1.2 Candidate-era material contract as a historical source record. It describes the source layer that was promoted into GLAZE UI V1.2 Stable and does not override the current V1.2 Stable lifecycle, acceptance boundary, or V1.3 deferred-qualification record.

GLAZE UI V1.2 preserves the V1.1 structural, semantic, accessibility, hierarchy, component, System Shell, and performance contracts while changing the default optical character of glazed surfaces.

## Governing visual rule

**Neutral glass is the material. Color is an accent.**

Ordinary glazed surfaces must read first as frosted white, pearl, clear-neutral, soft gray, or neutral dark glass. Blue, teal, green, aqua, amber, or other chromatic pigments must not become the default base tint of windows, panels, cards, menus, toolbars, sheets, dialogs, popovers, search surfaces, sidebars, quick settings, or shell chrome.

Semantic and brand colors remain available for active controls, focus, selection, progress, status, badges, icons, and product identity. They do not define the underlying glass substrate.

## Light appearance

The target character is milky, translucent, softly reflective glass with visible backdrop diffusion.

Reference material values:

- Base glass: `rgba(255, 255, 255, 0.58)`
- Raised glass: `rgba(255, 255, 255, 0.72)`
- Overlay glass: `rgba(250, 250, 250, 0.82)`
- Specular border: `rgba(255, 255, 255, 0.52)`
- Structural border: `rgba(80, 80, 80, 0.10)`
- Standard blur: `28px`
- Heavy blur: `44px`
- Backdrop saturation target: approximately `1.08–1.15`

The values are reference targets, not permission to weaken contrast or hierarchy.

## Dark and Deep Dark appearance

Dark Glaze remains translucent but becomes neutral graphite/smoke rather than blue-green.

Reference material values:

- Dark base: `rgba(25, 25, 27, 0.62)`
- Dark raised: `rgba(38, 38, 41, 0.72)`
- Dark overlay: `rgba(42, 42, 45, 0.82)`
- Dark specular border: `rgba(255, 255, 255, 0.12)`
- Deep Dark base: `rgba(14, 14, 16, 0.72)`
- Deep Dark overlay: `rgba(24, 24, 27, 0.86)`

A cool or warm environmental cast may appear indirectly through the backdrop, but the material itself remains neutral.

## Material hierarchy

The inherited material hierarchy remains **Canvas → Surface → Soft Glaze → Glaze → Deep Glaze → Live Glaze**.

V1.2 changes how glazed levels are optically differentiated:

- **Soft Glaze:** light diffusion, low-opacity neutral fill, subtle white edge.
- **Glaze:** stronger diffusion and a slightly more opaque neutral substrate.
- **Deep Glaze:** greater depth, broader shadow, stronger edge separation, still chromatically neutral.
- **Live Glaze:** may expose more environmental color from the backdrop or content, but must not paint a permanent teal/green base tint onto the material.

Depth should come from blur, opacity, luminance, border reflection, geometry, and shadow before hue.

## Frosted edge and depth language

Glaze surfaces should use:

- soft white or neutral specular highlights along upper/light-facing edges;
- faint inner edge illumination rather than hard outlines;
- broad low-opacity shadows rather than dense black strokes;
- rounded geometry and capsule treatments where appropriate;
- visual separation through opacity and depth before chromatic tint.

No glossy effect may obscure text, state, target boundaries, or focus.

## Color and atmosphere policy

The V1.1 Deep Teal + Soft Amber atmosphere becomes **optional accent atmosphere**, not the default material substrate.

For the V1.2 Candidate source layer:

- neutral material contribution is the dominant optical source;
- default material tint from teal, aqua, green, or amber is `0`;
- atmospheric aura may remain outside a surface or pass through the backdrop at low strength;
- selected, focused, active, semantic, or branded controls may use color intentionally;
- quick-settings and shell panels must be neutral glass with colored active states, not colored glass panels with brighter colored controls.

## Wallpaper and backdrop interaction

The material should allow bounded background color and form to diffuse through the surface. Background-derived color is an optical consequence of translucency, not a hard-coded panel pigment.

Environmental sampling remains local-only and optional. It must not infer protected semantics or transmit source imagery for derivation.

## 32-component material expansion

The Candidate source layer includes a machine-readable **component-material contract** for the complete inherited 32-component V1 catalog. The purpose is not to make every component translucent. It is to decide, component by component, where Frosted Neutral belongs and where Solid/Raised presentation remains authoritative.

The mapping is governed by these rules:

- **Reading surfaces remain Solid/Raised by default.** Cards, lists, tables, AI suggestions, AI answers, smart summaries, and similar content planes do not become glass simply because V1.2 introduces a new material style.
- **Consequential decision surfaces remain high-opacity by default.** Dialogs retain non-backdrop-dependent presentation so the material cannot compete with the decision itself.
- **Transient and floating chrome is the primary Frosted Neutral domain.** Popovers, menus, tooltips, sheets, toasts, docks, capsules, Smart Rail, Universal Search chrome, and explicitly floating navigation/toolbars may use Glaze or Deep Glaze.
- **Foundation controls are variant-driven.** Buttons, icon buttons, text fields, and selects only use Frosted Neutral when the explicit `glaze` variant is requested.
- **Persistent navigation remains Surface by default.** Sidebar and Navigation Rail gain Frosted Neutral only when rendered as detached/floating regions.
- **Live Glaze remains explicit.** Aurora Surface remains a normal content surface unless `data-material="live-glaze"` is intentionally selected.
- **Nested backdrop blur remains off by default.** Frosted controls nested inside an already glazed parent fall back to a neutral translucent fill without an additional backdrop-filter pass.
- **Accent color remains state-local.** Selection, current navigation, switch/choice state, progress, focus, and semantics may use color without recoloring the surrounding glass.

The Candidate-era component mapping is defined by `contracts/v1.2/component-materials.candidate.json`, implemented by `css/glaze-v1.2-components.candidate.css`, and exercised by `reference/v1.2/component-gallery.html`. The validator compares that mapping against `contracts/components/v1/catalog.json` and fails closed unless all 32 inherited components are represented exactly once.

## System Shell material expansion

V1.2 specializes the inherited five-region System Shell contract without replacing it. The exact inherited regions remain **workspace, navigation, universal-search, control-center, and critical-system**.

The shell mapping is governed as follows:

- **Workspace → Surface.** The workspace remains the primary content and reading plane and is not backdrop-blurred by default.
- **Navigation → Surface when persistent, Glaze when detached/floating.** A persistent rail or sidebar remains structural. Floating shell navigation may use regular Frosted Neutral Glaze.
- **Universal Search → Glaze entry + Deep Glaze results panel.** Search is transient command chrome; individual result rows do not add their own blur.
- **Control Center → one dominant Deep Glaze panel.** Quick-setting tiles, sliders, and local controls sit inside the parent panel as Raised/local surfaces and must not introduce nested backdrop blur.
- **Critical System → Raised, no backdrop blur.** Security, privacy, destructive, recovery, authentication, permission, and other consequential system decisions remain high-opacity and producer-authoritative.

The inherited shell budget is unchanged: one dominant Glaze panel plus up to three small floating Glaze controls. V1.2 cannot claim an extra material budget merely because the new glass is visually lighter.

Control Center active states use accent color mixed into a neutral Raised tile. Inactive tiles remain neutral. Semantic status colors remain authoritative to the system that owns the underlying truth and may replace the ordinary accent treatment only when backed by producer-authoritative state.

The System Shell Candidate-era source is defined by `contracts/v1.2/system-shell-materials.candidate.json`, implemented by `css/glaze-v1.2-system-shell.candidate.css`, and exercised by `reference/v1.2/system-shell.html`. Its region keys and material budgets are validated against `contracts/system-shell/glaze-system-shell-v1.json` so the promoted source cannot silently add or drop inherited shell regions.

## Accessibility and resilience

Reduced Transparency removes backdrop-dependent effects and falls back toward solid neutral surfaces while preserving hierarchy, contrast, boundaries, and state.

Forced Colors disables custom material pigmentation and custom optical edge treatment where required by the platform.

Increased Contrast strengthens boundaries before adding chroma.

Reduced Motion is independent of transparency and does not alter semantic state.

Critical reading and consequential-decision surfaces remain eligible for Solid/Raised treatment under the inherited material contract.

The component and System Shell expansions follow the same fallbacks: explicit frosted variants collapse toward neutral Solid/Raised presentation, nested glass does not accumulate blur, programmatic state remains intact when optical effects disappear, and 200% text reflows Control Center rather than shrinking targets.

## Performance

V1 material budgets remain inherited: one dominant Glaze region plus up to three small floating Glaze controls by default, with no default nested backdrop blur.

When performance degrades, reduce environmental effects and blur before degrading text, target size, state, focus, or semantic truth.

The component material layer disables a second backdrop-filter pass for Frosted Neutral children inside a glazed System Panel, System Overlay, Sheet, Popover, Menu, or Universal Search result panel. The System Shell layer applies the same rule to Control Center children and can fall back from heavy blur to standard blur, then to solid neutral shell surfaces.

## Historical Candidate implementation / promoted-source lineage

- Candidate-era tokens retained as promoted source: `tokens/glaze-v1.2-frosted-neutral.candidate.json`
- Candidate-era component-material contract retained as promoted source: `contracts/v1.2/component-materials.candidate.json`
- Candidate-era System Shell contract retained as promoted source: `contracts/v1.2/system-shell-materials.candidate.json`
- Candidate-era base web layer retained as promoted source: `css/glaze-v1.2-frosted-neutral.candidate.css`
- Candidate-era component layer retained as promoted source: `css/glaze-v1.2-components.candidate.css`
- Candidate-era System Shell layer retained as promoted source: `css/glaze-v1.2-system-shell.candidate.css`
- Historical Candidate preview entrypoint: `css/glaze-v1.2.0-candidate.css`
- Current Stable web entrypoint: `css/glaze-v1.2.0.css`
- Material reference: `reference/v1.2/frosted-neutral.html`
- 32-component gallery: `reference/v1.2/component-gallery.html`
- System Shell reference: `reference/v1.2/system-shell.html`
- Stable authority validator: `scripts/validate_glaze_v1.py`
- Promoted-source compatibility validator: `scripts/validate_glaze_v1_2_candidate.py`

During Candidate development, the preview layer was activated on the V1.1 Stable baseline with `data-glaze-upgrade="v1.2-frosted-neutral"` and did not change `VERSION`, `currentStable`, or downstream consumer eligibility. On 2026-09-06, the project owner promoted V1.2 to Stable and deferred the remaining external/manual/physical qualification work to V1.3. That deferral is not represented as passed V1.2 evidence, and downstream consumer conformance remains independent and fail-closed.

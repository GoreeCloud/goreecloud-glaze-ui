# GLAZE UI V1.3 — Adaptive Resonance

GLAZE UI V1.3 is GoreeCloud's current Official, Stable, consumer-eligible shared visual and interaction design system. **Beauty is a requirement, not a regression risk.** Machine version: **1.3.0**.

## Core rules

**Neutral glass is the material foundation. Adaptive expression is contextual, bounded, and subordinate to meaning, accessibility, and task completion.**

**Solid where users read or make explicit critical decisions. Glazed where users interact with transient navigation, command, search, control, or feedback chrome.**

V1.3 Adaptive Resonance builds on the V1.2 Living Frosted foundation with adaptive/dynamic color, expressive shape, responsive typography, Living Material 2.0 behavior, human reachability, adaptive navigation, multi-pane/foldable/desktop composition, System Shell evolution, contextual intelligence, motion/continuity, accessibility/resilience, Personalization, and signature component/reference coverage.

## Stable source authority

- `VERSION` — `1.3.0`
- `GLAZE_UI_V1_3.md` — official Stable contract
- `registry/lifecycle.json` — lifecycle authority
- `css/glaze-v1.3.0.css` — Stable web entrypoint
- `js/glaze-v1.3.0.mjs` — Stable runtime entrypoint
- `acceptance/v1.3-stable.md` — V1.3 Stable acceptance/scope record
- `MIGRATION_V1_2_TO_V1_3.md` — current migration control plane
- `consumers/registry.json` — current consumer target and adoption state

The promoted V1.3 source retains historical `.candidate` filenames internally where they identify implementation-stage provenance. Those filenames do not make the current lifecycle Candidate; the aggregate Stable entrypoints and lifecycle registry are authoritative.

## V1.4 development candidate

Glaze UI V1.4 is under active **proposed / implementation-candidate** development and does not replace V1.3 as the Stable consumer target.

The V1.4 Optical Material and Chromatic Depth foundation in `tokens/glaze-v1.4-optical-material.candidate.json` establishes bounded optical-depth, diffusion, refraction, ambient-tint, color-bleed, highlight-rim, shadow-depth, concentration, fallback, and component-profile contracts while preserving V1.3 token, radius, motion, accessibility, lifecycle, and adoption boundaries.

`contracts/v1.4/semantic-optical-runtime.candidate.json` keeps applications above raw optical values. It defines candidate material, frost, and elevation roles; explicit runtime capability negotiation; accepted/downgraded/substituted/rejected outcomes; first-class accessibility and performance profiles; privacy-preserving environmental-sampling boundaries; compositor degradation rules; and truthful authority separation for Wardveil Security, Privacy Shield, GoreeCloud Identity, Everkeep, and application-owned state. The semantic API remains explicitly candidate and is not frozen.

`js/glaze-v1.4-optical-runtime.candidate.mjs` implements the dependency-free semantic resolver. It resolves material/elevation/accessibility/performance/environment intent against explicitly declared runtime capabilities, records actual accepted state and fallback reasons, forces designed solid material for Reduced Transparency or unavailable translucency, degrades expensive effects before content correctness, and blocks adaptive environmental sampling on protected or privacy-restricted surfaces.

The bounded Web reference implementation is split into `js/glaze-v1.4-optical-web.candidate.mjs` and `css/glaze-v1.4-optical-runtime.candidate.css`. The Web adapter consumes accepted semantic-runtime state, projects it through `data-glaze-v14-*` attributes and bounded CSS flags, and leaves raw optical profile values internal to the candidate renderer. The stylesheet builds on the Stable V1.3 web entrypoint locally, is not imported by Stable V1.3, requires no remote assets, and preserves optical, static, and solid semantic rendering paths. It does not implement environmental pixel sampling and does not grant Glaze UI security, privacy, identity, recovery, or application-state authority.

Automated source-level evidence for runtime and Web behavior is provided by `tests/glaze-v1.4-optical-runtime.test.mjs`, `tests/glaze-v1.4-optical-web.test.mjs`, the paired Python contract regressions, and the exact-head `Glaze V1.4 Optical Runtime Candidate` workflow. Exact implementation head `1868e111431c60d80aefad38d360e15d3cc974bf` passed workflow run `34661235305`, including both V1.4 validators, both Python regression suites, the executable runtime/Web regressions, validator compilation, and the no-source-mutation check.

This is **source-level candidate evidence only**. It does not establish human visual acceptance, assistive-technology acceptance, browser-matrix qualification, physical-device qualification, native-renderer parity, production frame-time/GPU/power budgets, downstream consumer acceptance, or Stable V1.4 release status.

`VERSION` intentionally remains `1.3.0`. The V1.4 candidate has no lifecycle authority, is not consumer-eligible, grants no downstream conformance, and does not establish a Stable V1.4 release.

Source validation is governed by `scripts/validate_glaze_v1.4_optical_material.py`, `scripts/validate_glaze_v1_4_semantic_optical_runtime.py`, their paired Python regressions, the runtime/Web Node regressions, and `.github/workflows/glaze-v1.4-optical-material.yml`.

## V1.3.1 follow-up

On 2026-09-08 the GoreeCloud project owner directed that V1.3 become Official, Stable, and consumer-eligible on `main` and that unresolved release-quality work move to V1.3.1 instead of holding back V1.3.0.

The carry-forward work includes human optical/icon review, manual assistive-technology qualification, physical-device/native-platform qualification, physical-device production-performance qualification, native Personalization adapter qualification, and source-namespace/migration/rollback cleanup. None of that unfinished work is relabeled as passed V1.3.0 evidence.

See `GLAZE_UI_V1_3_1_HARDENING.md` and `acceptance/v1.3-deferred-qualification.md`.

## Consumer boundary

V1.3.0 is eligible for downstream adoption and is the required shared target. No downstream GoreeCloud application auto-becomes conformant or production-ready because V1.3 is Stable. Every applicable consumer must explicitly migrate to `1.3.0` and produce repository-local evidence for its actual platform, accessibility, performance, workflow, rollback, and release acceptance boundary.

GLAZE UI V1.2 / `1.2.0` remains preserved as the immediately preceding known-good Stable rollback anchor. Glaze Motion remains separately governed unless explicitly incorporated by a Stable contract.

## License

MIT. GoreeCloud branding and product identity remain subject to applicable project policies.

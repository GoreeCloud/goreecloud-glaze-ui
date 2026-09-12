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

`js/glaze-v1.4-optical-runtime.candidate.mjs` implements the dependency-free scalar semantic resolver. It resolves material/elevation/accessibility/performance/environment intent against explicitly declared runtime capabilities, records actual accepted state and fallback reasons, forces designed solid material for Reduced Transparency or unavailable translucency, degrades expensive effects before content correctness, and blocks adaptive environmental sampling on protected or privacy-restricted surfaces.

The composable accessibility layer in `contracts/v1.4/accessibility-composition.candidate.json` and `js/glaze-v1.4-accessibility-runtime.candidate.mjs` builds above that scalar primitive without removing it. `accessibilityRequirements` can preserve simultaneous Reduced Transparency, Increased Contrast, Reduced Motion, forced-colors, large-text, color-vision accommodation, and low-power/performance-constrained requirements. The legacy `accessibilityProfile` remains accepted as a compatibility summary, but it is not the behavior authority when composed requirements are present. Reduced Transparency still forces a designed solid material; contrast and forced-colors suppress optional atmospheric effects; Reduced Motion disables optional material motion; constrained-performance forces the efficient path; and large-text/color-vision requirements remain explicit for consuming layout and state-cue policy.

The bounded Web reference implementation is split into `js/glaze-v1.4-optical-web.candidate.mjs` and `css/glaze-v1.4-optical-runtime.candidate.css`. The Web adapter consumes the composable runtime state, projects independent `data-glaze-v14-a11y-*` attributes plus the retained summary accessibility attribute, and leaves raw optical profile values internal to the candidate renderer. The stylesheet builds on the Stable V1.3 web entrypoint locally, is not imported by Stable V1.3, requires no remote assets, preserves optical/static/solid semantic rendering paths, and uses system-color-compatible Canvas/CanvasText treatment for the candidate forced-colors path. It does not implement environmental pixel sampling and does not grant Glaze UI security, privacy, identity, recovery, or application-state authority.

The browser capability slice adds `contracts/v1.4/browser-capabilities.candidate.json` and `js/glaze-v1.4-browser-capabilities.candidate.mjs`. The adapter uses local, synchronous feature detection for bounded rendering capabilities and local media preferences. It fails closed when evidence is missing, never auto-declares environmental sampling, reflection, or HDR-aware luminance, and does not read browser identity, device-memory or hardware-concurrency values, battery/network details, screen dimensions, capture APIs, persistent storage, telemetry, or analytics. Browser-detected accessibility requirements are preserved additively and independently; forced-colors is not collapsed into Increased Contrast for behavior, while the legacy recommended profile remains only a compatibility summary and is explicitly not qualification evidence.

A local browser diagnostic surface is available at `reference/glaze-v1.4-browser-qualification.candidate.html` with its companion module `reference/glaze-v1.4-browser-qualification.candidate.mjs`. It exercises the candidate capability adapter and Web renderer locally and visibly identifies itself as a non-qualifying diagnostic. It does not persist or transmit results and does not establish browser-matrix, assistive-technology, physical-device, production-performance, consumer, or lifecycle acceptance.

The accessibility qualification-support layer adds `contracts/v1.4/accessibility-qualification.candidate.json`, `contracts/v1.4/accessibility-qualification-evidence.schema.candidate.json`, `scripts/evaluate_glaze_v1_4_accessibility_qualification.py`, and `evidence/v1.4/templates/accessibility-qualification-record.candidate.json`. Evidence records bind to exact source and source-tree revisions, record browser/OS/preference/assistive-technology observations, require evidence references for passing scenarios, fail closed on missing required coverage or unresolved high/critical issues, and require explicit human or combined review before the bounded accessibility slice can be accepted. The evaluator is read-only and deterministic: it may return blocked, review-ready, failed, or accepted for the accessibility qualification slice, but it can never grant Stable status, consumer conformance, browser-matrix qualification, or lifecycle-gate acceptance. The included template intentionally evaluates as blocked until real exact-source observations and authorized review are supplied.

`scripts/prepare_glaze_v1_4_accessibility_qualification_packet.py` provides a governed preparation path for real qualification sessions without manufacturing evidence. Prepared packets are confined to `artifacts/v1.4/accessibility-qualification-drafts/`, bind to an immutable source commit and tree, prefill only operator-supplied review/environment/support-claim metadata, keep human review pending, leave preference observations not-tested, and leave required scenarios not-tested. Claimed screen-reader, voice-control, or switch-control support converts the corresponding conditional scenario from not-applicable to not-tested so the claim cannot silently become acceptance. Each packet includes a capture checklist and must deterministically evaluate as blocked with both accessibility and lifecycle acceptance false until real observations and governed review are supplied.

Automated source-level evidence for the optical material, semantic runtime, composable accessibility runtime, Web renderer, browser capability, qualification-support, and packet-preparation slices is provided by five Python validators, six Python regression layers, `tests/glaze-v1.4-optical-runtime.test.mjs`, `tests/glaze-v1.4-accessibility-composition.test.mjs`, `tests/glaze-v1.4-optical-web.test.mjs`, `tests/glaze-v1.4-browser-capabilities.test.mjs`, and the exact-head `Glaze V1.4 Optical Runtime Candidate` workflow. Exact packet-preparation implementation head `afbe19f4822d43d8bfd9d7c8050ee5095e76f440` passed workflow run `34664300800`, including all five V1.4 validators, all six Python regression layers, the blocked/non-promoting qualification-template check, an exact-source/tree-bound temporary packet smoke test, executable runtime/accessibility/Web/browser Node regressions, validator/evaluator/generator compilation, and the no-source-mutation check.

This is **source-level candidate and qualification-support evidence only**. It establishes that the source behavior and evidence machinery are structurally tested; it does not establish human visual acceptance, real assistive-technology acceptance, browser-matrix qualification, physical-device qualification, native-renderer parity, production frame-time/GPU/power budgets, downstream consumer acceptance, or Stable V1.4 release status.

`VERSION` intentionally remains `1.3.0`. The V1.4 candidate has no lifecycle authority, is not consumer-eligible, grants no downstream conformance, and does not establish a Stable V1.4 release.

Source validation is governed by `scripts/validate_glaze_v1.4_optical_material.py`, `scripts/validate_glaze_v1_4_semantic_optical_runtime.py`, `scripts/validate_glaze_v1_4_browser_capabilities.py`, `scripts/validate_glaze_v1_4_accessibility_composition.py`, `scripts/validate_glaze_v1_4_accessibility_qualification.py`, `scripts/evaluate_glaze_v1_4_accessibility_qualification.py`, `scripts/prepare_glaze_v1_4_accessibility_qualification_packet.py`, their Python regressions, the runtime/accessibility/Web/browser Node regressions, and `.github/workflows/glaze-v1.4-optical-material.yml`.

## V1.3.1 follow-up

On 2026-09-08 the GoreeCloud project owner directed that V1.3 become Official, Stable, and consumer-eligible on `main` and that unresolved release-quality work move to V1.3.1 instead of holding back V1.3.0.

The carry-forward work includes human optical/icon review, manual assistive-technology qualification, physical-device/native-platform qualification, physical-device production-performance qualification, native Personalization adapter qualification, and source-namespace/migration/rollback cleanup. None of that unfinished work is relabeled as passed V1.3.0 evidence.

See `GLAZE_UI_V1_3_1_HARDENING.md` and `acceptance/v1.3-deferred-qualification.md`.

## Consumer boundary

V1.3.0 is eligible for downstream adoption and is the required shared target. No downstream GoreeCloud application auto-becomes conformant or production-ready because V1.3 is Stable. Every applicable consumer must explicitly migrate to `1.3.0` and produce repository-local evidence for its actual platform, accessibility, performance, workflow, rollback, and release acceptance boundary.

GLAZE UI V1.2 / `1.2.0` remains preserved as the immediately preceding known-good Stable rollback anchor. Glaze Motion remains separately governed unless explicitly incorporated by a Stable contract.

## License

MIT. GoreeCloud branding and product identity remain subject to applicable project policies.

# Glaze UI — Feature Roadmap

**Status:** Active roadmap control  
**As of:** 2026-09-11  
**Authoritative project record:** Project Specification — Glaze UI  
**Binding V1.4 plan:** Plan — Glaze UI V1.4 Optical Material and Chromatic Depth Upgrade  
**Canonical repository:** GoreeCloud/goreecloud-glaze-ui  
**Drive control:** `GoreeCloud/Feature Roadmap/Glaze UI/FEATURE-ROADMAP.docx`

## Purpose

This file is the repository-side feature roadmap control for Glaze UI. It records current planned and recommended feature work without replacing the authoritative project record, implementation evidence, release gates, or GoreeCloud Tasks Management.

## Roadmap

| ID | Feature / obligation | Priority | Current state |
| --- | --- | --- | --- |
| FR-001 | Reconcile and maintain every current planned or recommended Glaze UI feature from the authoritative project record and verified repository evidence in this roadmap. | High | Ongoing control |
| FR-002 | Move actionable feature obligations into GoreeCloud Tasks Management when required, preserving priority, dependency, and lifecycle disposition. | High | Ongoing control |
| FR-003 | Do not mark features implemented, complete, cancelled, or superseded without authoritative evidence and synchronized repository/Drive roadmap updates. | High | Ongoing control |
| FR-004 | Develop Glaze UI V1.4 as a non-breaking refinement of Stable V1.3, preserving V1.3 contracts, tokens, accessibility behavior, motion semantics, radii, and consumer lifecycle boundaries until independently promoted. | P0 | Active development — proposed / implementation-candidate; Stable remains 1.3.0 |
| FR-005 | Establish the V1.4 Optical Material and Chromatic Depth contract for bounded optical depth, diffusion, refraction, ambient tint, color bleed, highlight rim, shadow depth, and derived material concentration. | P0 | Source implementation candidate added on `upgrade/glaze-ui-v1.4-optical-material-20260911`; source validation gate added; not Stable or consumer-eligible |
| FR-006 | Apply bounded V1.4 optical profiles across the planned surface, elevated-surface, panel, side-panel, shelf, menu, popover, menu-bar, card, list-row, search-field, selector, toolbar, header, footer, dialog, and toast component families. | P0 | Candidate profile mapping implemented; physical/native qualification not established |
| FR-007 | Preserve fail-safe accessibility and performance behavior: reduced-transparency solid fallback, inherited reduced-motion behavior, static/solid low-performance fallback, and diffusion-only fallback where refraction is unsupported. | P0 | Candidate contract, executable resolver, renderer, and regressions enforce bounded fallbacks; browser/device qualification pending |
| FR-008 | Continue V1.4 secondary refinement work for typography, motion, responsive/form-factor behavior, window chrome, performance, and accessibility only where consistent with the binding V1.4 plan and without forcing spatial/AR frameworks. | High | Planned / not established by the current optical-runtime slices |
| FR-009 | Establish a semantic optical runtime contract so consumers request material/elevation/accessibility intent instead of binding directly to raw optical values, and require runtimes to report accepted, downgraded, substituted, or rejected outcomes. | P0 | Contract plus executable semantic resolver implemented as candidate; API remains candidate/not frozen; exact-head automated validation green |
| FR-010 | Enforce privacy-preserving environmental sampling, truthful operational-state authority, accessibility-first degradation, and non-claimed performance/native qualification in the V1.4 runtime contract. | P0 | Contract and executable resolver enforce local/ephemeral sampling boundaries, protected/privacy-restricted surface blocking, accessibility fallbacks, and truth-authority separation; platform qualification pending |
| FR-011 | Provide a bounded Web reference renderer for accepted V1.4 semantic optical state without exposing raw optical values as the consumer contract or granting visual-layer operational authority. | P0 | Dedicated candidate Web adapter and stylesheet implemented at `js/glaze-v1.4-optical-web.candidate.mjs` and `css/glaze-v1.4-optical-runtime.candidate.css`; exact-head runtime/Web regressions green; browser/device visual qualification pending |
| FR-012 | Maintain deterministic capability negotiation and fallback regression coverage for V1.4 optical runtime and Web rendering behavior. | P0 | Python contract validators plus executable runtime/Web regressions remain in the exact-head V1.4 CI gate; production/native acceptance not established |
| FR-013 | Add a privacy-bounded browser capability adapter that detects only local, synchronous rendering capabilities and accessibility/appearance preferences, fails closed on missing evidence, and avoids browser identity, hardware fingerprinting, network, capture, persistence, telemetry, and analytics. | P0 | `contracts/v1.4/browser-capabilities.candidate.json` and `js/glaze-v1.4-browser-capabilities.candidate.mjs` implemented as candidates; source validation green; environmental sampling, reflection, and HDR are never auto-declared |
| FR-014 | Provide a local browser diagnostic/qualification harness that exercises the candidate browser adapter and Web renderer without representing diagnostics as browser-matrix, assistive-technology, device, performance, consumer, or release qualification. | High | Local candidate harness implemented at `reference/glaze-v1.4-browser-qualification.candidate.html` with companion module; source regressions green; real browser/device qualification remains pending |
| FR-015 | Compose simultaneous V1.4 accessibility requirements instead of collapsing Reduced Transparency, Increased Contrast, Reduced Motion, forced-colors, large-text, color-vision accommodation, and constrained-performance behavior into a single mutually exclusive profile. | P0 | `contracts/v1.4/accessibility-composition.candidate.json` and `js/glaze-v1.4-accessibility-runtime.candidate.mjs` implemented; browser requirements compose additively; Web renderer exposes independent accessibility state; exact implementation head `d6858b35b5c87ef8600580e3a6e68450bcdb0786` passed dedicated run `34662883331` |
| FR-016 | Qualify composed accessibility behavior across real browser, operating-system preference, forced-colors/high-contrast, assistive-technology, and representative device combinations without treating feature detection as acceptance evidence. | P0 | Planned qualification work; source composition behavior is automated and green, but browser-matrix, assistive-technology, and physical-device qualification remain unestablished |

## V1.4 current implementation boundary

The repository currently contains bounded V1.4 source, executable runtime, composable accessibility, Web reference-renderer, and browser-capability candidates, not a V1.4 release. The candidates are rooted in Stable `1.3.0`, keep `VERSION` at `1.3.0`, have no lifecycle authority, are not consumer-eligible, and cannot establish downstream V1.4 conformance.

Current source artifacts for the V1.4 optical-runtime, accessibility-composition, Web-renderer, and browser-capability slices are:

- `tokens/glaze-v1.4-optical-material.candidate.json`
- `contracts/v1.4/semantic-optical-runtime.candidate.json`
- `contracts/v1.4/browser-capabilities.candidate.json`
- `contracts/v1.4/accessibility-composition.candidate.json`
- `js/glaze-v1.4-optical-runtime.candidate.mjs`
- `js/glaze-v1.4-accessibility-runtime.candidate.mjs`
- `js/glaze-v1.4-optical-web.candidate.mjs`
- `js/glaze-v1.4-browser-capabilities.candidate.mjs`
- `css/glaze-v1.4-optical-runtime.candidate.css`
- `reference/glaze-v1.4-browser-qualification.candidate.html`
- `reference/glaze-v1.4-browser-qualification.candidate.mjs`
- `scripts/validate_glaze_v1.4_optical_material.py`
- `scripts/validate_glaze_v1_4_semantic_optical_runtime.py`
- `scripts/validate_glaze_v1_4_browser_capabilities.py`
- `scripts/validate_glaze_v1_4_accessibility_composition.py`
- `tests/test_glaze_v1.4_optical_material.py`
- `tests/test_glaze_v1_4_semantic_optical_runtime.py`
- `tests/test_glaze_v1_4_browser_capabilities.py`
- `tests/test_glaze_v1_4_accessibility_composition.py`
- `tests/glaze-v1.4-optical-runtime.test.mjs`
- `tests/glaze-v1.4-accessibility-composition.test.mjs`
- `tests/glaze-v1.4-optical-web.test.mjs`
- `tests/glaze-v1.4-browser-capabilities.test.mjs`
- `.github/workflows/glaze-v1.4-optical-material.yml`

The scalar semantic runtime remains available for compatibility and resolves candidate material/elevation/accessibility/performance/environment intent against explicitly declared runtime capabilities. The accessibility-composition layer builds above it and preserves simultaneous requirements in `accessibilityRequirements`; the retained scalar `accessibilityProfile` becomes a compatibility summary rather than the behavior authority when composed requirements are present. Reduced Transparency can force a solid semantic surface while forced-colors/increased contrast, Reduced Motion, and efficient-performance requirements continue to apply independently.

The bounded Web renderer consumes the composed accepted state through a dedicated JavaScript adapter and candidate stylesheet. It projects independent accessibility data attributes, preserves optical/static/solid fallback paths, uses a system-color-compatible forced-colors treatment, requires no remote assets, is not imported by the Stable V1.3 entrypoint, and does not implement environmental pixel sampling or create security, privacy, identity, recovery, or application-state authority.

The browser capability adapter adds local, synchronous feature detection for bounded CSS/Web Animation support and local accessibility/appearance media preferences. It fails closed if evidence is absent; never auto-declares environmental sampling, reflection, or HDR-aware luminance; and does not inspect browser identity, device-memory/hardware-concurrency values, battery/network details, screen dimensions, capture APIs, persistent storage, telemetry, or analytics. Browser-detected accessibility requirements are preserved additively and independently for composition rather than being silently reduced to one behavior profile.

The local browser diagnostic harness exercises those candidate paths without persisting or transmitting results and without converting local detection into a browser-matrix or release claim.

Exact implementation head `d6858b35b5c87ef8600580e3a6e68450bcdb0786` passed dedicated workflow run `34662883331`. The gate verified the exact checked-out revision, all four V1.4 validators, all four Python regression layers, executable runtime/accessibility/Web/browser Node regressions, validator compilation, and no tracked-source mutation. This is source-level evidence only.

Human visual acceptance, assistive-technology acceptance, browser matrix qualification, physical-device qualification, native-renderer parity, production frame-time/GPU/power budgets, consumer migration evidence, and Stable V1.4 lifecycle promotion remain outside the evidence established by these candidates.

## Maintenance and synchronization

This roadmap and the corresponding Drive `FEATURE-ROADMAP.docx` must remain materially synchronized with one another and with the authoritative project or service record. Update both copies whenever feature scope, priority, dependency, implementation status, cancellation, supersession, recommendation, or verification state materially changes.

No feature may be represented as complete or Stable solely because it appears in this roadmap. Completion and lifecycle claims require the applicable authoritative implementation, validation, review, release, and production evidence.

## Reconciliation rule

At each material feature change, reconcile this roadmap against the current authoritative project record, repository implementation state, applicable platform-system requirements, and GoreeCloud Tasks Management. Missing obligations, stale status, duplicated work, roadmap drift, or undocumented disposition changes are defects to correct.

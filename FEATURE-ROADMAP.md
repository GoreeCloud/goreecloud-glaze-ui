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
| FR-015 | Compose simultaneous V1.4 accessibility requirements instead of collapsing Reduced Transparency, Increased Contrast, Reduced Motion, forced-colors, large-text, color-vision accommodation, and constrained-performance behavior into a single mutually exclusive profile. | P0 | `contracts/v1.4/accessibility-composition.candidate.json` and `js/glaze-v1.4-accessibility-runtime.candidate.mjs` implemented; browser requirements compose additively; Web renderer exposes independent accessibility state; source behavior is now explicitly recorded as automated-test verified while real qualification flags remain false |
| FR-016 | Qualify composed accessibility behavior across real browser, operating-system preference, forced-colors/high-contrast, assistive-technology, and representative device combinations without treating feature detection as acceptance evidence. | P0 | Qualification-support infrastructure is implemented and source-verified; real browser/OS/AT observations and authorized review acceptance remain pending |
| FR-017 | Establish a canonical, exact-source V1.4 accessibility qualification evidence contract, draft record format, and deterministic fail-closed evaluator that can distinguish blocked, review-ready, failed, and accessibility-slice-accepted records without granting lifecycle promotion. | P0 | `contracts/v1.4/accessibility-qualification.candidate.json`, evidence schema, evaluator, validator, template, and regressions implemented; evaluator always keeps lifecycle-gate acceptance false |
| FR-018 | Capture and review actual V1.4 accessibility evidence against the governed qualification contract for required preference, keyboard/focus, large-text/reflow, color-independent state, and claimed screen-reader/voice/switch scenarios. | P0 | Preparation tooling now exists, but real evidence execution remains pending; no browser/OS/AT/device qualification is claimed until actual observations, evidence references, and authorized human/combined review are supplied |
| FR-019 | Provide a governed qualification packet generator that binds a draft to an immutable source commit/tree, confines output to the draft area, emits a capture checklist, and cannot fabricate observations, evidence references, qualification acceptance, consumer conformance, or lifecycle promotion. | P0 | `scripts/prepare_glaze_v1_4_accessibility_qualification_packet.py` and packet regressions implemented; exact implementation/workflow-scope head `e3b3996c25e7636e399c2ed763b7c9b75cc4b90c` passed dedicated run `34664367694`; packet implementation was first verified at `afbe19f4822d43d8bfd9d7c8050ee5095e76f440` in run `34664300800` |

## V1.4 current implementation boundary

The repository currently contains bounded V1.4 source, executable runtime, composable accessibility, Web reference-renderer, browser-capability, accessibility-qualification-support, and qualification-packet-preparation candidates, not a V1.4 release. The candidates are rooted in Stable `1.3.0`, keep `VERSION` at `1.3.0`, have no lifecycle authority, are not consumer-eligible, and cannot establish downstream V1.4 conformance.

Current source artifacts for the V1.4 optical-runtime, accessibility-composition, Web-renderer, browser-capability, accessibility-qualification-support, and packet-preparation slices are:

- `tokens/glaze-v1.4-optical-material.candidate.json`
- `contracts/v1.4/semantic-optical-runtime.candidate.json`
- `contracts/v1.4/browser-capabilities.candidate.json`
- `contracts/v1.4/accessibility-composition.candidate.json`
- `contracts/v1.4/accessibility-qualification.candidate.json`
- `contracts/v1.4/accessibility-qualification-evidence.schema.candidate.json`
- `js/glaze-v1.4-optical-runtime.candidate.mjs`
- `js/glaze-v1.4-accessibility-runtime.candidate.mjs`
- `js/glaze-v1.4-optical-web.candidate.mjs`
- `js/glaze-v1.4-browser-capabilities.candidate.mjs`
- `css/glaze-v1.4-optical-runtime.candidate.css`
- `reference/glaze-v1.4-browser-qualification.candidate.html`
- `reference/glaze-v1.4-browser-qualification.candidate.mjs`
- `evidence/v1.4/templates/accessibility-qualification-record.candidate.json`
- `scripts/validate_glaze_v1.4_optical_material.py`
- `scripts/validate_glaze_v1_4_semantic_optical_runtime.py`
- `scripts/validate_glaze_v1_4_browser_capabilities.py`
- `scripts/validate_glaze_v1_4_accessibility_composition.py`
- `scripts/validate_glaze_v1_4_accessibility_qualification.py`
- `scripts/evaluate_glaze_v1_4_accessibility_qualification.py`
- `scripts/prepare_glaze_v1_4_accessibility_qualification_packet.py`
- `tests/test_glaze_v1.4_optical_material.py`
- `tests/test_glaze_v1_4_semantic_optical_runtime.py`
- `tests/test_glaze_v1_4_browser_capabilities.py`
- `tests/test_glaze_v1_4_accessibility_composition.py`
- `tests/test_glaze_v1_4_accessibility_qualification.py`
- `tests/test_glaze_v1_4_accessibility_qualification_packet.py`
- `tests/glaze-v1.4-optical-runtime.test.mjs`
- `tests/glaze-v1.4-accessibility-composition.test.mjs`
- `tests/glaze-v1.4-optical-web.test.mjs`
- `tests/glaze-v1.4-browser-capabilities.test.mjs`
- `.github/workflows/glaze-v1.4-optical-material.yml`

The scalar semantic runtime remains available for compatibility and resolves candidate material/elevation/accessibility/performance/environment intent against explicitly declared runtime capabilities. The accessibility-composition layer builds above it and preserves simultaneous requirements in `accessibilityRequirements`; the retained scalar `accessibilityProfile` becomes a compatibility summary rather than the behavior authority when composed requirements are present. Reduced Transparency can force a solid semantic surface while forced-colors/increased contrast, Reduced Motion, and efficient-performance requirements continue to apply independently.

The bounded Web renderer consumes the composed accepted state through a dedicated JavaScript adapter and candidate stylesheet. It projects independent accessibility data attributes, preserves optical/static/solid fallback paths, uses a system-color-compatible forced-colors treatment, requires no remote assets, is not imported by the Stable V1.3 entrypoint, and does not implement environmental pixel sampling or create security, privacy, identity, recovery, or application-state authority.

The browser capability adapter adds local, synchronous feature detection for bounded CSS/Web Animation support and local accessibility/appearance media preferences. It fails closed if evidence is absent; never auto-declares environmental sampling, reflection, or HDR-aware luminance; and does not inspect browser identity, device-memory/hardware-concurrency values, battery/network details, screen dimensions, capture APIs, persistent storage, telemetry, or analytics. Browser-detected accessibility requirements are preserved additively and independently for composition rather than being silently reduced to one behavior profile.

The local browser diagnostic harness exercises those candidate paths without persisting or transmitting results and without converting local detection into a browser-matrix or release claim.

The accessibility qualification-support layer adds an exact-source evidence schema and deterministic evaluator. Required qualification scenarios cover runtime/source identity, multi-preference composition, Reduced Transparency, Increased Contrast, Reduced Motion, forced-colors, large-text/reflow, keyboard/focus order, and color-independent semantic state; screen-reader, voice-control, and switch-control scenarios become mandatory when those support claims are asserted. Passing observations require evidence references, missing or not-tested required coverage blocks progression, any required/claimed failure fails the slice, unresolved high/critical issues block acceptance, and automated-only review cannot accept the slice. Even a valid human/combined accepted accessibility record cannot grant lifecycle-gate acceptance, Stable V1.4, consumer conformance, browser-matrix qualification, physical-device qualification, or production-performance qualification.

The packet-preparation layer turns that contract into a safe qualification-session starting point. It binds each prepared record to an exact commit and tree, accepts only explicit review/environment/support-claim metadata, keeps review pending, leaves all required preference and scenario evidence untested, converts claimed assistive-technology scenarios to not-tested rather than passing them, emits a capture checklist, confines generated files to `artifacts/v1.4/accessibility-qualification-drafts/`, and requires the prepared record to evaluate as blocked. It therefore reduces manual setup error without manufacturing evidence or expanding lifecycle authority.

Exact implementation/workflow-scope head `e3b3996c25e7636e399c2ed763b7c9b75cc4b90c` passed dedicated workflow run `34664367694`. The gate verified the exact checked-out revision, all five V1.4 validators, all six Python regression layers, the blocked/non-promoting qualification-template invariant, an exact-source/tree-bound generated packet smoke test, executable runtime/accessibility/Web/browser Node regressions, validator/evaluator/generator compilation, and no tracked-source mutation. Packet behavior itself had already passed the same expanded gate at `afbe19f4822d43d8bfd9d7c8050ee5095e76f440` in run `34664300800`; `e3b3996c...` adds only the workflow push-path correction. This is source-level candidate and qualification-support evidence only.

Human visual acceptance, real assistive-technology acceptance, browser matrix qualification, physical-device qualification, native-renderer parity, production frame-time/GPU/power budgets, consumer migration evidence, and Stable V1.4 lifecycle promotion remain outside the evidence established by these candidates.

## Maintenance and synchronization

This roadmap and the corresponding Drive `FEATURE-ROADMAP.docx` must remain materially synchronized with one another and with the authoritative project or service record. Update both copies whenever feature scope, priority, dependency, implementation status, cancellation, supersession, recommendation, or verification state materially changes.

No feature may be represented as complete or Stable solely because it appears in this roadmap. Completion and lifecycle claims require the applicable authoritative implementation, validation, review, release, and production evidence.

## Reconciliation rule

At each material feature change, reconcile this roadmap against the current authoritative project record, repository implementation state, applicable platform-system requirements, and GoreeCloud Tasks Management. Missing obligations, stale status, duplicated work, roadmap drift, or undocumented disposition changes are defects to correct.

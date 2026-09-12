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
| FR-007 | Preserve fail-safe accessibility and performance behavior: reduced-transparency solid fallback, inherited reduced-motion behavior, static/solid low-performance fallback, and diffusion-only fallback where refraction is unsupported. | P0 | Candidate contract, executable resolver, and regressions enforce bounded fallbacks; device qualification pending |
| FR-008 | Continue V1.4 secondary refinement work for typography, motion, responsive/form-factor behavior, window chrome, performance, and accessibility only where consistent with the binding V1.4 plan and without forcing spatial/AR frameworks. | High | Planned / not established by the current optical-runtime slices |
| FR-009 | Establish a semantic optical runtime contract so consumers request material/elevation/accessibility intent instead of binding directly to raw optical values, and require runtimes to report accepted, downgraded, substituted, or rejected outcomes. | P0 | Contract plus executable semantic resolver implemented as candidate; API remains candidate/not frozen; exact-head automated validation green |
| FR-010 | Enforce privacy-preserving environmental sampling, truthful operational-state authority, accessibility-first degradation, and non-claimed performance/native qualification in the V1.4 runtime contract. | P0 | Contract and executable resolver enforce local/ephemeral sampling boundaries, protected/privacy-restricted surface blocking, accessibility fallbacks, and truth-authority separation; platform qualification pending |
| FR-011 | Provide a bounded Web reference adapter for resolved V1.4 semantic optical state without exposing raw optical values or granting visual-layer operational authority. | P0 | Candidate `applyOpticalRuntime()` adapter implemented with dataset/CSS-state projection; source-level regressions green; browser/device visual qualification pending |
| FR-012 | Maintain deterministic capability negotiation and fallback regression coverage for V1.4 optical runtime behavior. | P0 | Node runtime regressions plus Python contract validators are integrated into the exact-head V1.4 CI gate; production/native acceptance not established |

## V1.4 current implementation boundary

The repository currently contains bounded V1.4 source and executable candidates, not a V1.4 release. The candidates are rooted in Stable `1.3.0`, keep `VERSION` at `1.3.0`, have no lifecycle authority, are not consumer-eligible, and cannot establish downstream V1.4 conformance.

Current source artifacts for the V1.4 optical-runtime slices are:

- `tokens/glaze-v1.4-optical-material.candidate.json`
- `contracts/v1.4/semantic-optical-runtime.candidate.json`
- `js/glaze-v1.4-optical-runtime.candidate.mjs`
- `scripts/validate_glaze_v1.4_optical_material.py`
- `scripts/validate_glaze_v1_4_semantic_optical_runtime.py`
- `tests/test_glaze_v1.4_optical_material.py`
- `tests/test_glaze_v1_4_semantic_optical_runtime.py`
- `tests/glaze-v1.4-optical-runtime.test.mjs`
- `.github/workflows/glaze-v1.4-optical-material.yml`

The semantic runtime now resolves candidate material/elevation/accessibility/performance/environment intent against explicitly declared runtime capabilities. It records accepted runtime state and downgrade/substitution reasons, preserves designed solid material fallbacks, blocks adaptive sampling on protected or privacy-restricted surfaces, and exposes a bounded Web reference adapter. It does not expose raw optical property values as the application-facing contract and does not create security, privacy, identity, recovery, or application-state authority.

Exact-head automated validation covers both V1.4 contract validators, their Python regressions, the executable Node runtime regression suite, validator compilation, and a no-source-mutation check. This is source-level evidence only.

Human visual acceptance, assistive-technology acceptance, physical-device qualification, browser matrix qualification, native-renderer parity, production frame-time/GPU/power budgets, consumer migration evidence, and Stable V1.4 lifecycle promotion remain outside the evidence established by these candidates.

## Maintenance and synchronization

This roadmap and the corresponding Drive `FEATURE-ROADMAP.docx` must remain materially synchronized with one another and with the authoritative project or service record. Update both copies whenever feature scope, priority, dependency, implementation status, cancellation, supersession, recommendation, or verification state materially changes.

No feature may be represented as complete or Stable solely because it appears in this roadmap. Completion and lifecycle claims require the applicable authoritative implementation, validation, review, release, and production evidence.

## Reconciliation rule

At each material feature change, reconcile this roadmap against the current authoritative project record, repository implementation state, applicable platform-system requirements, and GoreeCloud Tasks Management. Missing obligations, stale status, duplicated work, roadmap drift, or undocumented disposition changes are defects to correct.

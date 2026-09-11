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
| FR-007 | Preserve fail-safe accessibility and performance behavior: reduced-transparency solid fallback, inherited reduced-motion behavior, static/solid low-performance fallback, and diffusion-only fallback where refraction is unsupported. | P0 | Candidate contract and validator enforce fallback presence; runtime/device qualification pending |
| FR-008 | Continue V1.4 secondary refinement work for typography, motion, responsive/form-factor behavior, window chrome, performance, and accessibility only where consistent with the binding V1.4 plan and without forcing spatial/AR frameworks. | High | Planned / not established by the current optical-material slice |

## V1.4 current implementation boundary

The repository currently contains a bounded V1.4 source candidate, not a V1.4 release. The candidate is rooted in Stable `1.3.0`, keeps `VERSION` at `1.3.0`, has no lifecycle authority, is not consumer-eligible, and cannot establish downstream V1.4 conformance.

Current source artifacts for the first V1.4 slice are:

- `tokens/glaze-v1.4-optical-material.candidate.json`
- `scripts/validate_glaze_v1.4_optical_material.py`
- `tests/test_glaze_v1.4_optical_material.py`
- `.github/workflows/glaze-v1.4-optical-material.yml`

Physical-device qualification, native-renderer parity, production frame-time/GPU/power budgets, and Stable V1.4 lifecycle promotion remain outside the evidence established by this candidate.

## Maintenance and synchronization

This roadmap and the corresponding Drive `FEATURE-ROADMAP.docx` must remain materially synchronized with one another and with the authoritative project or service record. Update both copies whenever feature scope, priority, dependency, implementation status, cancellation, supersession, recommendation, or verification state materially changes.

No feature may be represented as complete or Stable solely because it appears in this roadmap. Completion and lifecycle claims require the applicable authoritative implementation, validation, review, release, and production evidence.

## Reconciliation rule

At each material feature change, reconcile this roadmap against the current authoritative project record, repository implementation state, applicable platform-system requirements, and GoreeCloud Tasks Management. Missing obligations, stale status, duplicated work, roadmap drift, or undocumented disposition changes are defects to correct.

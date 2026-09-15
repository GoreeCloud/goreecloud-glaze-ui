# Glaze UI — Feature Roadmap

**Status:** Active roadmap control  
**As of:** 2026-09-15  
**Authoritative project record:** Project Specification — Glaze UI  
**Canonical repository:** `GoreeCloud/goreecloud-glaze-ui`  
**Drive control:** `GoreeCloud/Feature Roadmap/Glaze UI/FEATURE-ROADMAP.docx`

## Purpose

This file is the repository-side feature roadmap control for Glaze UI. It records current planned and recommended feature work without replacing authoritative implementation evidence, exact-revision validation, release gates, GoreeCloud Tasks Management, or the Drive-side roadmap control.

The current Official Stable release is **GLAZE UI V1.4.1 / `1.4.1`**. The V1.4.1 Extended Upgrade architecture is being developed as the successor **GLAZE UI V1.5 / `1.5.0-dev.1`** line so the published V1.4.1 Stable identity is not redefined. V1.5 remains **Development**, **non-consumer-eligible**, **non-RC**, and **non-Stable**.

## Current verified direction

The V1.5 Development line now contains the governed Context + Capability Resolution architecture, fail-closed provider authority/provenance handling, Privacy Shield-owned data-use authorization presentation, capability-aware composition/navigation/controls, accessibility-priority composition, explicit graceful degradation, privacy-safe explainable diagnostics, continuity handling, anti-jitter stabilization, representative GoreeCloud consumer profiles, and fail-closed external-review planning tooling.

Machine functional coverage is 78 Development scenarios: 39 core + 8 action/degradation + 7 diagnostics + 10 unified-resolution + 14 representative-consumer scenarios. The stabilization-review planning layer defines six external evidence areas and eighteen pending review obligations. Those obligations are planning requirements, not acceptance passes.

Repository-local V1.5 Development compatibility checkpoints are verified for GoreeCloud Reader, GoreeCloud Launcher, and GoreeCloud Manager. These checkpoints do not establish rendered/native V1.5 acceptance, consumer conformance, Release Candidate status, Stable status, deployment, or production acceptance. The current GoreeCloud Security Center and GoreeCloud Privacy Center repositories contain only README-level source and therefore cannot yet supply meaningful repository-local V1.5 consumer acceptance evidence.

## Roadmap

| ID | Feature / obligation | Priority | Current state |
| --- | --- | --- | --- |
| FR-001 | Reconcile and maintain every current planned or recommended Glaze UI feature from the authoritative project record and verified repository evidence in this roadmap. | High | Ongoing control |
| FR-002 | Move actionable feature obligations into GoreeCloud Tasks Management when required, preserving priority, dependency, blocker, and lifecycle disposition. | High | Ongoing control |
| FR-003 | Do not mark features implemented, complete, cancelled, superseded, RC, Stable, deployed, or production-accepted without authoritative evidence and synchronized repository/Drive/task records. | High | Ongoing control |
| FR-004 | Preserve GLAZE UI V1.4.1 / `1.4.1` as the current Official Stable authority and known-good shared baseline while V1.5 remains an isolated successor Development stream. | P0 | Active control — Stable authority preserved; V1.5 does not redefine V1.4.1. |
| FR-005 | Complete the V1.5 Context + Capability Resolution architecture with bounded context normalization, governed capability state/provenance, fail-closed provider authority, capability-aware presentation, accessibility precedence, continuity, explainable diagnostics, graceful degradation, and anti-jitter behavior. | P0 | Development implementation and machine conformance substantially implemented; 78 functional scenarios are covered. External acceptance remains separate. |
| FR-006 | Maintain privacy and authority boundaries so Glaze presents authoritative state but never creates consent, grants permissions, invents provider precedence, executes consequential operations, or upgrades security/privacy/recovery truth. | P0 | Machine-verified Development boundary; Privacy Shield and provider-owned authority remain external to Glaze execution authority. |
| FR-007 | Expand repository-local V1.5 compatibility across representative GoreeCloud consumers while preserving each consumer's truthful implemented Glaze source mapping and current Stable requirement. | P0 | Reader, Launcher, and Manager Development checkpoints verified. Security Center and Privacy Center are currently README-only and cannot yet provide substantive consumer evidence. Additional implemented consumers remain eligible for bounded compatibility work. |
| FR-008 | Execute exact-revision external stabilization review across human usability, assistive technology/accessibility, representative target-device/runtime behavior, privacy/authorization boundaries, anti-jitter/performance, and platform/posture/input/window adaptation. | P0 | Pending. Fail-closed planning contract/generator/verifier now define 6 evidence areas / 18 obligations without manufacturing evidence or acceptance. |
| FR-009 | Qualify an exact V1.5 Release Candidate only after required repository-local integration and external stabilization evidence are complete, reviewed, and governed approval explicitly authorizes RC transition. | P0 | Blocked on FR-007 and FR-008 evidence. No RC claim. |
| FR-010 | Promote V1.5 to Stable only after exact RC qualification, required human/policy approval, exact release evidence, post-merge verification, documentation reconciliation, rollback readiness, and explicit downstream adoption boundaries. | P0 | Not started as a lifecycle transition. Current Stable remains V1.4.1. |
| FR-011 | Complete the separately governed V1.4.1 immutable tag/GitHub Release publication path without conflating publication with V1.5 stabilization or downstream consumer acceptance. | High | Pending governed publication approval/verification in Tasks Management. |

## Stabilization evidence boundary

Machine checks may prove source behavior, contract integrity, exact-revision preservation, or planning-tool integrity only to the extent those checks exercise them. They do not substitute for required human review, assistive-technology sessions, representative device/runtime evidence, privacy/policy review, performance qualification, repository-local consumer acceptance, lifecycle approval, deployment, or production acceptance.

A generated V1.5 stabilization-review packet must remain pending until a real review is performed against the exact source revision. Missing evidence, unknown authority, duplicate authority, stale evidence, or source-revision mismatch must fail closed rather than being inferred as acceptable.

## Maintenance and synchronization

This roadmap and the corresponding Drive `FEATURE-ROADMAP.docx` must remain materially synchronized with one another and with the authoritative project record, current repository state, and GoreeCloud Tasks Management. Update both copies whenever feature scope, priority, dependency, implementation status, blocker, cancellation, supersession, recommendation, or verification state materially changes.

No feature may be represented as complete or Stable solely because it appears in this roadmap. Completion and lifecycle claims require the applicable authoritative implementation, validation, review, release, and production evidence.

## Reconciliation rule

At each material feature change, reconcile this roadmap against the current authoritative project record, repository implementation state, applicable Platform System requirements, consumer evidence, and GoreeCloud Tasks Management. Missing obligations, stale status, duplicated work, roadmap drift, or undocumented disposition changes are defects to correct.

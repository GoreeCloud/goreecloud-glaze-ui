# GLAZE UI V1.3 Qualification Review Worksheets

These worksheets are preparation aids only. They never confer `passed`, lifecycle acceptance, Candidate status, Stable status, consumer eligibility, or conformance. Only create a top-level `evidence/v1.3/*.json` record after the corresponding exact-revision review is complete and truthfully dispositioned.

The first five worksheets are **pre-Candidate** and must all use one identical Candidate-qualification SHA. The sixth worksheet is **post-Candidate/pre-Stable** and uses the later exact Stable-promotion SHA while preserving the qualified Candidate SHA as provenance.

## Human optical + visual finish + icon/artwork collision

**Workstream:** `human-optical-and-icon-collision-qualification`  
**Stage:** Pre-Candidate  
**Accepted authority:** human or combined  
**Mandatory quality authority:** `contracts/v1.3/quality-rules.candidate.json`

- Candidate-qualification SHA:
- Reviewer / authority:
- Review date/time:
- Build or preview reference:

Checklist:
- [ ] All 55 rule IDs `quality-01` through `quality-55` reviewed against the exact source revision.
- [ ] Visual Finish Gate accepted: composition, spacing, optical alignment, hierarchy, typography, geometry, color, material, icons, motion, interaction/accessibility states, responsiveness, Light, Dark, and Deep Dark are visually complete.
- [ ] Blandness Rejection Gate accepted: no reviewed major experience is reasonably described as bland, boring, dry, generic, sterile, unfinished, dated, lifeless, or visually weak.
- [ ] Beauty Without Usability Loss accepted.
- [ ] Accessibility-as-Beauty reviewed under applicable reduced-transparency, reduced-motion, increased-contrast, forced-colors, large-text/reflow, and related modes.
- [ ] Responsive Beauty reviewed across claimed compact, medium, expanded, workspace, foldable/posture, and far-view environments.
- [ ] Final Quality Test accepted for clarity, deliberate composition, personality, current visual language, tactility, hierarchy, spacing, material conviction, icon/type balance, polished states, accessibility presentation, and personalization identity.
- [ ] Light, Dark, Deep Dark, Clarity, and Expression profiles reviewed.
- [ ] Representative reference scenes, signature surfaces, and distinctive moments reviewed.
- [ ] Rest, hover, focus, pressed, selected, disabled, loading, error, success, empty, dragging, editing, reduced-transparency, reduced-motion, and increased-contrast states reviewed where applicable.
- [ ] Compact icons/artwork checked for collision, clipping, washout, illegibility, apparent-weight mismatch, and optical misalignment.
- [ ] Material thickness, diffusion, lighting, specular behavior, depth hierarchy, and Solid/Glaze restraint reviewed.
- [ ] Scroll, overlay, focus, selection, cardification, capsule saturation, effect saturation, and visual-monoculture risks reviewed.
- [ ] Unresolved material visual defects block a pass.

## Manual assistive technology

**Workstream:** `manual-assistive-technology-qualification`  
**Stage:** Pre-Candidate  
**Accepted authority:** human or combined

- Candidate-qualification SHA:
- Reviewer / authority:
- Claimed support matrix:
- Review date/time:

Checklist:
- [ ] Screen-reader sessions completed where claimed.
- [ ] Voice-control sessions completed where claimed.
- [ ] Switch-control sessions completed where claimed.
- [ ] Keyboard navigation and focus order checked where applicable.
- [ ] Large text / zoom / reflow interaction checked where applicable.
- [ ] Semantics, labels, state announcements, and focus restoration checked.
- [ ] Issues and dispositions recorded with inspectable references.

## Physical-device + native-platform

**Workstream:** `physical-device-native-platform-qualification`  
**Stage:** Pre-Candidate  
**Required authority:** combined

- Candidate-qualification SHA:
- Human reviewer / authority:
- Automated evidence source:
- Review date/time:
- Device/OS/compositor/posture inventory:

Checklist:
- [ ] Android/OEM behavior checked where claimed.
- [ ] Linux compositor/window-system behavior checked where claimed.
- [ ] Foldable/posture behavior checked where claimed.
- [ ] Pointer, keyboard, touch, and far-view behavior checked where applicable.
- [ ] Native-platform variance documented.
- [ ] Failures/fallbacks documented and dispositioned.

Physical-device claims require physical-device observations; emulation alone is insufficient.

## Physical-device production performance

**Workstream:** `physical-device-production-performance-qualification`  
**Stage:** Pre-Candidate  
**Required authority:** combined

- Candidate-qualification SHA:
- Reviewer / authority:
- Accepted performance budget reference:
- Review date/time:

Checklist:
- [ ] Frame pacing measured on representative physical devices.
- [ ] Interaction latency measured.
- [ ] Memory usage measured.
- [ ] GPU/compositor behavior measured where available.
- [ ] Power/thermal behavior measured where applicable.
- [ ] Constrained-device behavior measured.
- [ ] Effects degrade before correctness/task completion.
- [ ] Measurement method, sample window, device state, and raw references retained.

## Native Personalization adapter

**Workstream:** `native-personalization-adapter-qualification`  
**Stage:** Pre-Candidate  
**Accepted authority:** human or combined

- Candidate-qualification SHA:
- Reviewer / authority:
- Claimed native adapters/platforms:
- Review date/time:

Checklist where claimed:
- [ ] Persistence behavior verified.
- [ ] System-appearance adapter behavior verified.
- [ ] Wallpaper-source adapter verified without raw wallpaper transmission/telemetry.
- [ ] Failure and fallback behavior verified.
- [ ] Accessibility overrides remain authoritative over personalization.
- [ ] No Glaze-owned cross-device sync claim introduced.
- [ ] Unsupported adapters are explicitly marked not claimed rather than assumed.

## Stable activation + source-namespace cleanup

**Workstream:** `stable-activation-and-source-namespace-cleanup`  
**Stage:** Post-Candidate / pre-Stable  
**Required authority:** combined

- Qualified Candidate SHA:
- Exact Stable-promotion SHA:
- Candidate lifecycle observed active: [ ]
- Reviewer / authority:
- Automated namespace inventory reference:
- Review date/time:

Checklist:
- [ ] The Candidate is actually active before this review begins.
- [ ] `qualified_candidate_source_revision` matches the five-track qualified Candidate SHA.
- [ ] `stable_promotion_source_revision` matches the exact source revision under Stable review.
- [ ] Candidate-name inventory captured.
- [ ] Reviewed migration map prepared for every renamed/promoted source.
- [ ] Byte/pixel/behavior equivalence established where required.
- [ ] Import/reference closure validated.
- [ ] Rollback path verified.
- [ ] No lifecycle promotion is inferred from this worksheet or evidence record.
- [ ] Consumer repositories remain independently governed.

`python scripts/audit_glaze_v1_3_namespace.py` may provide inventory input, but automation alone does not accept this workstream. Final Stable readiness is evaluated separately with `scripts/evaluate_glaze_v1_3_stable_readiness.mjs`.

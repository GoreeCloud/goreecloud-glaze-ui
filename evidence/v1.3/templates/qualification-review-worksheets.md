# GLAZE UI V1.3 Qualification Review Worksheets

These worksheets are preparation aids for the six blocking qualification tracks. They are intentionally Markdown and stored below `evidence/v1.3/templates/` so validators do not interpret them as accepted qualification records.

They never confer `passed`, lifecycle acceptance, Candidate status, consumer eligibility, or conformance. Only create a top-level `evidence/v1.3/*.json` record after the corresponding exact-revision review is complete and explicitly dispositioned under `contracts/v1.3/qualification-evidence.schema.json`.

## Human optical + visual finish + icon/artwork collision

**Workstream:** `human-optical-and-icon-collision-qualification`  
**Accepted authority:** human or combined  
**Mandatory quality authority:** `contracts/v1.3/quality-rules.candidate.json`

- Promotion-candidate SHA:
- Reviewer / authority:
- Review date/time:
- Build or preview reference:

Checklist:
- [ ] All 55 rule IDs `quality-01` through `quality-55` reviewed against the exact source revision.
- [ ] Visual Finish Gate accepted: composition, spacing, optical alignment, hierarchy, typography, geometry, color, material, icons, motion, interaction/accessibility states, responsiveness, Light, Dark, and Deep Dark are visually complete.
- [ ] Blandness Rejection Gate accepted: no reviewed major experience is reasonably described as bland, boring, dry, generic, sterile, unfinished, dated, lifeless, or visually weak.
- [ ] Beauty Without Usability Loss accepted: no aesthetic treatment reduces readability, obscures state, shrinks targets, slows task completion, weakens focus/navigation/contrast, or creates motion dependency.
- [ ] Accessibility Is Part of Beauty reviewed under Reduced Transparency, Reduced Motion, Increased Contrast, Forced Colors, large text/reflow, and other applicable modes.
- [ ] Responsive Beauty reviewed across the claimed compact, medium, expanded, workspace, foldable/posture, and far-view environments.
- [ ] Final Quality Test accepted for clarity, deliberate composition, personality, current visual language, tactility, hierarchy, spacing, material conviction, icon/type optical balance, polished states, accessibility presentation, and personalization identity.
- [ ] Light appearance reviewed.
- [ ] Dark appearance reviewed.
- [ ] Deep Dark appearance reviewed.
- [ ] Clarity and Expression profiles reviewed.
- [ ] Representative reference scenes reviewed.
- [ ] Signature surfaces and distinctive moments reviewed, including applicable Navigation Capsule, Universal Search, Control Center, primary actions, media controls, and contextual surfaces.
- [ ] Microstates reviewed: rest, hover, focus, pressed, selected, disabled, loading, error, success, empty, dragging, editing, reduced transparency, reduced motion, and increased contrast where applicable.
- [ ] Compact-size icons/artwork checked for collision, clipping, washout, illegibility, apparent-weight mismatch, and optical misalignment.
- [ ] Material thickness, diffusion, lighting, specular behavior, depth hierarchy, and Solid/Glaze restraint reviewed.
- [ ] Scroll, overlay, focus, selection, cardification, capsule saturation, effect saturation, and visual-monoculture risks reviewed.
- [ ] Issues have inspectable references and dispositions; unresolved material visual defects block a pass.

A passed evidence record must use `schema_version: 2` and populate `quality_review` with the quality contract path, all 55 rule IDs, and every required acceptance flag set to `true`. Automation cannot supply the human acceptance judgment.

## Manual assistive technology

**Workstream:** `manual-assistive-technology-qualification`  
**Accepted authority:** human or combined

- Promotion-candidate SHA:
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
**Required authority:** combined

- Promotion-candidate SHA:
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
**Required authority:** combined

- Promotion-candidate SHA:
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
- [ ] Degradation confirms effects reduce before correctness/task completion.
- [ ] Measurement method, sample window, device state, and raw references retained.

Desktop CI or synthetic unit tests alone do not establish physical-device production performance.

## Native Personalization adapter

**Workstream:** `native-personalization-adapter-qualification`  
**Accepted authority:** human or combined

- Promotion-candidate SHA:
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
**Required authority:** combined

- Promotion-candidate SHA:
- Reviewer / authority:
- Automated namespace inventory reference:
- Review date/time:

Checklist:
- [ ] Candidate-name inventory captured.
- [ ] Reviewed migration map prepared for every renamed/promoted source.
- [ ] Byte/pixel/behavior equivalence established where required.
- [ ] Import/reference closure validated.
- [ ] Rollback path verified.
- [ ] Candidate release-entrypoint activation remains separate until governed promotion.
- [ ] Consumer repositories remain independently governed.

`python scripts/audit_glaze_v1_3_namespace.py` may provide inventory input, but automation alone does not accept this workstream.

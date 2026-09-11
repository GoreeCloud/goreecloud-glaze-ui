# GLAZE UI V1.3 Supporting Runtime Evidence — Posture + Accessibility Resolver

**Evidence class:** supporting runtime corroboration only  
**Observed target:** GLAZE UI V1.3 / `1.3.0-candidate`  
**Observed source revision:** `72ad63bf32d80420b25dc98bfd2def47bcc2a427`  
**Observation date:** 2026-09-07  
**Browser context:** Firefox local reference suite at `http://127.0.0.1:8080/reference/v1.3/signature-components-and-compositions.html`  
**Lifecycle authority:** none — this record does not activate Candidate, promote Stable, or satisfy a governed workstream by itself.

## Purpose

Corroborate the frozen V1.3 resolver at runtime across compact posture/occlusion cases and accessibility presentation overrides. This is supporting evidence for later human optical, assistive-technology, and physical-device review; it is not a substitute for those required sessions.

## Observed matrix

| Case | Posture | Navigation | Detached | Forced in-flow | Min target | Search | Material | Reflow | Immediate motion | Blur allowed | Direction | Boundary |
| --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| baseline-flat | flat | `navigation-capsule` | true | false | 48 | `reachable-overlay-or-dedicated-view` | `glaze` | false | false | true | ltr | `component-required` |
| large-text-half-open | half-open | `navigation-capsule-in-flow` | false | true | 48 | `dedicated-view` | `glaze` | true | false | true | ltr | `component-required` |
| touch-assist-folded | folded | `navigation-capsule-in-flow` | false | true | 56 | `reachable-overlay-or-dedicated-view` | `glaze` | false | false | true | ltr | `component-required` |
| safe-area-folded | folded | `navigation-capsule-in-flow` | false | true | 48 | `reachable-overlay-or-dedicated-view` | `glaze` | false | false | true | ltr | `component-required` |
| keyboard-occluded | half-open | `navigation-capsule-in-flow` | false | true | 48 | `reachable-overlay-or-dedicated-view` | `glaze` | false | false | true | ltr | `component-required` |
| content-occluded | unfolded | `navigation-capsule-in-flow` | false | true | 48 | `reachable-overlay-or-dedicated-view` | `glaze` | false | false | true | ltr | `component-required` |
| reduced-motion | unfolded | `persistent-sidebar` | false | false | 48 | `overlay-panel` | `glaze` | false | true | true | ltr | `component-required` |
| reduced-transparency | unknown | `persistent-sidebar` | false | false | 48 | `overlay-panel` | `solid-neutral` | false | false | false | ltr | `component-required` |
| forced-colors | flat | `persistent-sidebar` | false | false | 48 | `overlay-panel` | `solid-neutral` | false | false | false | ltr | `accessibility-required` |
| rtl-contrast | unfolded | `persistent-sidebar` | false | false | 48 | `overlay-panel` | `glaze` | false | false | true | rtl | `accessibility-required` |

## Result

**PASS — supporting resolver/runtime sub-gate.**

The observed runtime behavior matched the frozen V1.3 contract in the areas exercised:

- compact navigation stayed detached only in the unobstructed baseline case;
- large text/reflow forced compact navigation into flow and changed Search to `dedicated-view`;
- touch assistance forced compact navigation in-flow and raised the interaction floor to 56 px;
- safe-area obstruction, keyboard occlusion, and visible-content occlusion each forced compact navigation in-flow;
- reduced motion made shell transitions immediate;
- reduced transparency replaced glaze material with `solid-neutral` and disabled blur;
- forced colors likewise used `solid-neutral`, disabled blur, and elevated boundaries to `accessibility-required`;
- increased-contrast/show-boundaries in RTL preserved RTL direction while elevating boundary strength.

## Evidence boundary

This record is deliberately stored beneath `evidence/v1.3/supporting/` rather than as an accepted `schema_version: 2` qualification JSON record. It does **not** establish:

- human optical acceptance;
- screen-reader or other assistive-technology acceptance;
- physical-device/native-platform acceptance;
- physical production-performance acceptance;
- native Personalization adapter acceptance;
- Candidate activation or Stable promotion.

The screenshots were supplied interactively during the qualification session and transcribed into the matrix above. Because the image attachments themselves are not committed here as immutable repository artifacts, this record must remain supporting/non-gating evidence.

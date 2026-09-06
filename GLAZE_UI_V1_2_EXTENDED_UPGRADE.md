# GLAZE UI V1.2 — Extended Upgrade / Living Frosted

**Lifecycle:** Candidate expansion of GLAZE UI V1.2 / `1.2.0-candidate`  
**Stable baseline:** GLAZE UI V1.1 / `1.1.0`  
**Consumer eligible:** No  
**Release theme:** Living Frosted  
**Promotion effect:** None by documentation or source presence alone.

This repository record binds the governed Living Frosted implementation tranche to the existing GLAZE UI V1.2 Frosted Neutral Candidate. It does not replace `GLAZE_UI_V1_2_CANDIDATE.md`, change `VERSION`, promote Experimental Glaze Motion, establish human acceptance, or authorize downstream consumer migration.

## Governing rules

- **Material:** Neutral glass is the material. Color is an accent.
- **Interaction:** Glass should respond when the user interacts with it.
- **Ergonomics:** Primary actions should move toward the user, not require the user to reach for them.
- **Continuity:** Context should transform before it disappears.

Together: **Glass carries interaction. Structure carries content. Motion carries continuity. Reachability carries usability.**

## Candidate source authority added by this tranche

- `contracts/v1.2/living-glaze.candidate.json` — umbrella Living Frosted behavior, optical response, clarity, performance tiers, and evidence boundary.
- `contracts/v1.2/adaptive-navigation.candidate.json` — semantic navigation transformations and Navigation Capsule behavior.
- `contracts/v1.2/ergonomic-layout.candidate.json` — reachability zones and recomposition inputs.
- `contracts/v1.2/context-continuity.candidate.json` — state preservation and connected transformation semantics.
- `contracts/v1.2/control-center-customization.candidate.json` — configurable/resizable Control Center semantics without nested backdrop blur.
- `contracts/v1.2/foldable-adaptation.candidate.json` — folded/unfolded, hinge, and task-continuity behavior.
- `contracts/v1.2/component-experience.candidate.json` — experience dimensions extending the inherited component-material contract.
- `contracts/v1.2/motion-integration.candidate.json` — Stable-compatible motion semantics that do not require Experimental Glaze Motion.
- `tokens/glaze-v1.2-living-material.candidate.json` — clarity, backdrop, thickness, interaction, and performance-tier values.
- `tokens/glaze-v1.2-interaction.candidate.json` — deterministic Living Glaze state values.
- `tokens/glaze-v1.2-navigation.candidate.json` — Navigation Capsule and recomposition values.
- `tokens/glaze-v1.2-ergonomics.candidate.json` — reachability and touch-target values.
- `tokens/glaze-v1.2-motion-integration.candidate.json` — bounded semantic motion values.
- `css/glaze-v1.2-living-glaze.candidate.css` — bounded web presentation and accessibility/performance fallbacks.
- `js/glaze-v1.2-living-glaze.candidate.mjs` — deterministic runtime attribute API; it accepts bounded producer/renderer complexity state and performs no image sampling.
- `reference/v1.2/living-glaze.html` — Living Glaze material/interaction/navigation lab.
- `scripts/validate_glaze_v1_2_living_glaze.py` and `.github/workflows/glaze-v1.2-living-glaze.yml` — fail-closed Candidate validation.

## Implemented in the bounded Candidate tranche

The source now establishes deterministic Clear/Balanced/Dense clarity profiles; canonical Living Glaze interaction states; Tier 3 → 2 → 1 → 0 degradation semantics; explicit privacy-safe backdrop-complexity inputs; one-handed interaction zones; Navigation Capsule semantics; context-preservation requirements; Control Center configuration contracts; foldable continuity; component-experience dimensions; and a Stable-compatible motion contract.

The web reference provides bounded hover/focus/press/drag/disabled responses, Reduced Motion behavior, Forced Colors behavior, Reduced Transparency behavior, touch-target floors, and performance-tier degradation. These are Candidate implementation/source-evidence claims only.

## Still required before Release Candidate or Stable

RC and Stable remain fail-closed until repository governance and exact-revision evidence establish all applicable gates, including:

- project-owner/human optical acceptance of exact rendered revision;
- human-approved V1.2 visual baselines and perceptual thresholds;
- assistive-technology/manual accessibility acceptance;
- production compositor/GPU/memory/power/thermal evidence on representative constrained hardware;
- representative native/OEM/form-factor qualification, including real foldable behavior where claimed;
- remaining personalization persistence, sync, system-resolution, and wallpaper interaction work where required;
- released artwork/sound/haptics mappings and applicable real-device acceptance;
- exact-revision release evidence and lifecycle promotion decisions;
- downstream consumer migration and consumer-specific acceptance after V1.2 itself is eligible.

No green source validator, reference scene, CI run, or repository document may substitute for these gates.

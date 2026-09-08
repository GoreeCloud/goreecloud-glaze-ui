# GLAZE UI V1.3.1 — Accessibility, Interaction + Qualification Hardening

**Status:** Active follow-up hardening  
**Lifecycle authority:** Separate future patch decision  
**Current Stable:** GLAZE UI V1.3 — Adaptive Resonance / `1.3.0`  
**Current Stable consumer eligibility:** Yes  
**V1.3.1 consumer eligibility:** No until separately released  
**Source line:** Official GLAZE UI V1.3 / `1.3.0` Stable

V1.3.1 is the governed follow-up track for hardening work that should not hold GLAZE UI V1.3.0 back from being Official, Stable, and consumer-eligible. It strengthens the released V1.3 line without rewriting V1.3.0 evidence history or pretending unfinished human/manual/physical-device work has passed.

## Owner-directed carry-forward scope

The following workstreams were previously treated as V1.3 lifecycle blockers and are now V1.3.1 obligations:

1. Human optical, visual-finish, and icon/artwork collision qualification, including all V1.3 quality rules.
2. Manual assistive-technology sessions for the support matrix actually claimed.
3. Physical-device/native-platform qualification for claimed Android/OEM, Linux compositor/window, foldable/posture, and other platform behavior.
4. Accepted production-performance budgets plus representative real-device pacing, latency, memory, GPU/compositor, power/thermal, and constrained-device evidence.
5. Native Personalization persistence, system-appearance, wallpaper-source, and fallback adapter qualification where claimed.
6. Stable activation/source-namespace cleanup with migration, equivalence, import-closure, and rollback hardening.

These obligations remain unresolved until real evidence exists. Their transfer to V1.3.1 is a release-scope decision, not an evidence pass.

## Accessibility and interaction hardening slice

The first implemented V1.3.1 slice makes the interaction layer explicit and machine-testable:

- visible keyboard, remote, and assistive-input focus with pointer focus remaining quiet until focus-visible;
- focus presentation structurally distinct from current, selected, and pressed state;
- fine-pointer-only hover lift, bounded pressed feedback, and disabled-state precedence;
- Reduced Motion removal of nonessential hover and press transforms without delaying semantic activation;
- Forced Colors focus through platform `Highlight` authority and structural state boundaries;
- Reduced Transparency solid-surface fallback for the reference treatment;
- 48px default interactive target floor and conservative 56px coarse-pointer reference floor;
- compact responsive wrapping without shrinking targets or depending on hover;
- a dependency-free browser reference for manual inspection; and
- fail-closed runtime, contract, CSS-marker, reference, and lifecycle-boundary validation.

## Implementation artifacts

- `contracts/v1.3.1/accessibility-interaction-hardening.candidate.json`
- `js/glaze-v1.3.1-accessibility-interaction-hardening.candidate.mjs`
- `css/glaze-v1.3.1-accessibility-interaction-hardening.candidate.css`
- `reference/v1.3/accessibility-interaction-hardening.html`
- `tests/glaze-v1.3.1-accessibility-interaction-hardening.test.mjs`
- `scripts/validate_glaze_v1_3_1_accessibility_interaction_hardening.py`
- `.github/workflows/glaze-v1.3.1-accessibility-interaction-hardening.yml`

## Acceptance boundary

Automated checks establish implementation contracts and reference behavior only. They do not establish human optical acceptance, screen-reader acceptance, switch/voice acceptance, physical-device acceptance, native-platform parity, production-performance acceptance, or downstream consumer conformance.

V1.3.0 remains Official Stable while V1.3.1 hardening proceeds. V1.3.1 requires its own future lifecycle decision before it becomes a Stable consumer target.

## Release relationship

- V1.3.0: current Official/Stable/consumer-eligible release.
- V1.3.1: active hardening and deferred-qualification follow-up.
- V1.2.0: retained historical Stable rollback baseline.

No V1.3.1 artifact may silently replace the V1.3.0 Stable entrypoints before a separate governed V1.3.1 release action.

# GLAZE UI Token Authority

GLAZE UI V1.2 / `1.2.0` is the current Stable GoreeCloud design-system and consumer target. `tokens/glaze-v1.json` is the current Stable token manifest. V1.1 / `1.1.0` remains the prior Stable rollback and audit baseline; its retained token files remain available where historical verification or rollback requires them.

V1.2 was promoted from its qualified Candidate source layer without renaming every source file. Candidate-suffixed V1.2 token and contract filenames are therefore **promoted Stable source provenance**, not evidence that V1.2 is still an active Candidate. During Candidate development those sources were non-consumer-eligible; that historical boundary remains encoded in the frozen source documents and compatibility validators without overriding the live `1.2.0` lifecycle.

`tokens/glaze-v1.2-core.candidate.json` remains the bounded V1.2 ownership and composition index used by the promoted source layer: it points semantic token families to their existing source files and does not duplicate raw token values or create a competing value authority. The current Stable lifecycle and consumer target are controlled by `VERSION`, `registry/lifecycle.json`, `tokens/glaze-v1.json`, and the V1.2 Stable entrypoints.

The promoted core source consolidates ownership for optical color references, atmosphere, material, frost, blur, material opacity, spacing, density, radius, shadow/elevation, typography, Crystal icon size/stroke, Motion duration, inherited semantic-color meanings, V1.2 interaction/state semantics through `tokens/glaze-v1.2-states.candidate.json`, and V1.2 form-factor adaptation semantics through `tokens/glaze-v1.2-form-factor.candidate.json`.

The V1.2 state-token owner preserves the established V1 hover, pressed, selected, disabled, and focus calibration while adding explicit loading, semantic, offline, and recovery truth requirements. Stable promotion does not authorize color-only state communication or allow token aliases to manufacture producer-owned truth.

The V1.2 form-factor token owner centralizes semantic composition states, input-modality rules, safe-area policy, and task-continuity requirements. Within this model, capability-class selection remains platform-adapter owned. Numeric gutter and density authority remains in the spatial-foundation token owner, so the form-factor layer references rather than duplicates those values. Stable source promotion establishes design-system token authority; it does not by itself establish downstream native parity, product production acceptance, physical-device qualification, or consumer conformance.

Token presence or alias resolution alone does not establish downstream V1.2 conformance or production eligibility. Each consumer must explicitly target `1.2.0` and produce fresh exact-revision application/platform evidence. Human/manual/physical qualification explicitly deferred from V1.2 remains V1.3 work and is not represented as passed V1.2 evidence.

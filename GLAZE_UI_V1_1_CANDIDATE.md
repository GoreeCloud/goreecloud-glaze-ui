# GLAZE UI V1.1 — Specification-Stable Candidate — Historical Record

Historical status: **Superseded Candidate record; V1.1 was later promoted to Stable**  
Candidate version: **1.1.0-candidate.1**  
Official target at Candidate publication: **GLAZE UI V1.0 / 1.0.0**  
Current Stable authority: **GLAZE UI V1.1 / 1.1.0**

This document preserves the repository-side implementation contract for the V1.1 optical-refinement Candidate before its governed Stable promotion. It is historical evidence and does not describe the repository's current lifecycle boundary. Current authority is defined by `registry/lifecycle.json`, `VERSION`, and the Stable contract `GLAZE_UI_V1_1.md`.

At Candidate publication, this record did not promote V1.1 to the current product identity, Stable release, Production Stable implementation, or downstream conformance target. V1.1 was subsequently promoted through a separate governed release process; that later Stable state does not retroactively change the Candidate-stage evidence recorded here.

## Purpose

V1.1 was designed as an incremental optical refinement of the V1 generation. It sharpened lighting, curvature, atmosphere, hierarchy, density presentation, state rendering, and visual acceptance while preserving V1 semantics, accessibility, material restraint, form-factor requirements, and source-of-truth boundaries.

The defining shared atmosphere was **Deep Teal + Soft Amber** over neutral graphite structure.

## Frozen Candidate boundaries

The V1.1 Candidate did not, by that Candidate state:

- promote Glaze Motion from its separately governed Experimental lifecycle;
- expand the canonical V1 component catalog;
- add or reinterpret protected security, privacy, identity, resilience, coordination, connectivity, or status semantics;
- allow default nested backdrop blur or unbounded decorative refraction;
- require environmental content sampling;
- make Muted Coral a canonical V1.1 atmospheric color;
- change the then-current `VERSION` or lifecycle records.

## Machine contracts

The Candidate was defined by:

- `contracts/v1.1/optical-refinement.candidate.json`
- `tokens/glaze-v1.1-atmosphere.candidate.json`
- `scripts/validate_glaze_v1_1_candidate.py`
- `acceptance/v1.1-specification-candidate.md`

At Candidate publication, the then-current V1 contracts remained authoritative until a separately governed V1.1 release promotion occurred. That promotion later occurred; current lifecycle authority must therefore be read from the active lifecycle records rather than this historical Candidate document.

## Resolution order

V1.1 Candidate presentation resolved in this order:

1. producer-authoritative protected semantic meaning;
2. Forced Colors;
3. Reduced Motion;
4. Reduced Transparency;
5. Increased Contrast and boundary visibility;
6. Large Text, 200% text scaling, Touch Assistance, and accessibility geometry;
7. material clarity and platform capability;
8. V1.1 atmosphere, application identity, and personalization.

Atmosphere always yielded before semantics, focus, accessibility, or hierarchy.

## Material compatibility

The V1.1 Candidate preserved the V1 structural material baseline. Functional glass remained bounded by the current material contract of that Candidate period, nested backdrop stacks remained disallowed by default, durable readable content did not require transparency, and the default material budget remained one dominant Glaze panel plus up to three small floating Glaze controls.

Atmospheric tint and Aura were presentation contributions layered over the material contract. They were never replacements for material opacity, semantic state, or foreground contrast.

## Candidate stability meaning

“Specification-Stable Candidate” meant the design decisions were sufficiently bounded and machine-readable for consistent implementation and validation. It did **not** mean Production Stable.

At that stage, V1.1 could become the official current target only after exact-revision validation, canonical reference scenes, accessibility and performance acceptance, human optical review, platform-native evidence where claimed, synchronized documentation, and a separate governed release/lifecycle promotion. That governed promotion later established V1.1 / `1.1.0` as the current Stable authority; downstream consumer conformance remains independently acceptance-gated.

# GLAZE UI Stability Authority

**Current Stable:** GLAZE UI V1.3 — Adaptive Resonance / `1.3.0`  
**Promotion date:** 2026-09-07  
**Prior known-good Stable rollback:** GLAZE UI V1.2 / `1.2.0`

The machine-readable lifecycle authority is `registry/lifecycle.json`; the version authority is `VERSION`.

## Current Stable boundary

GLAZE UI V1.3.0 is the current Stable shared design-system release under the bounded project-owner lifecycle decision recorded in `acceptance/v1.3-stable.md`.

Stable means the promoted V1.3 design-system source is the current official consumer-eligible release. It does **not** mean every pre-promotion external/manual/physical/native qualification item was completed. Missing or pending evidence remains missing or pending and is carried forward to `acceptance/v1.3.1-hardening.md`.

Stable source authority includes:

- `GLAZE_UI_V1_3.md` — product contract;
- `tokens/glaze-v1.3.json` — Stable V1.3 token-family manifest;
- `js/glaze-v1.3.0.mjs` — Stable runtime entrypoint;
- `css/glaze-v1.2.0.css` — inherited validated web material/base layer; V1.3 does not fabricate a new monolithic CSS aggregate;
- `acceptance/v1.3-stable.md` — lifecycle promotion record; and
- `registry/lifecycle.json` + `VERSION` — current machine lifecycle authority.

Historical `.candidate` filenames inside the promoted implementation remain source-stage names and are not, by themselves, evidence that the product lifecycle is Candidate.

## V1.3.1 hardening boundary

The unresolved V1.3 qualification obligations are active V1.3.1 maintenance work. They include fresh human optical review where required, manual assistive-technology qualification, physical/native/OEM/compositor/foldable/posture validation, production performance/resource evidence, native Personalization adapter validation, and Stable source-namespace/equivalence cleanup.

V1.3.1 hardening does not revoke V1.3.0 Stable status. A future V1.3.1 release requires its own governed patch promotion.

## Consumer boundary

A Stable Glaze release is eligible for independent consumer adoption, but Glaze UI never grants application conformance or product production eligibility by implication. Each consumer must validate its own exact revision, supported platforms, rendered/native behavior, accessibility, product workflows, performance, rollback, and production approval.

## Historical stability records

Earlier Stable and reset records remain preserved in `registry/lifecycle.json` and their corresponding acceptance/contract files. Historical acceptance results must not be rewritten to match the current lifecycle label.

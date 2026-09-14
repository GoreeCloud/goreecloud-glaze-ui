# GLAZE UI V1.4.1 Human Review Harness

This directory contains the deterministic review surface for real V1.4.1 human observation.

## Authority boundary

`optical-human-review.html` is a **review surface only**. It does not record human acceptance, does not write a V1.4.1 evidence record, does not mark checks passed, and cannot make the patch promotion eligible.

The harness uses only repository-local resources:

- `css/glaze-v1.4.0.css` — current Stable visual baseline.
- `js/glaze-v1.4.1.candidate.mjs` — additive V1.4.1 Candidate runtime under review.

It performs no telemetry, analytics, camera access, remote context lookup, or external asset loading.

## Exact-revision review

Serve the repository through a local static HTTP server and open the harness with the exact tested revision in the query string:

```text
reference/v1.4.1/optical-human-review.html?revision=<40-character-tested-revision>
```

The banner must display the same revision that is actually checked out. A missing or malformed revision leaves the surface visibly **UNBOUND** and must not be used as exact-revision evidence.

## Session 001

The first review surface supports human observation of:

- Content-Aware Frost.
- Semantic Blur Protection.
- Environment tint.
- Chromatic depth.
- Environmental color memory.
- Reduced Transparency.
- Increased Contrast.
- Forced Colors.
- Reduced Motion.
- Keyboard behavior.
- Pointer behavior.
- Glass quality.
- Depth/warmth quality.
- Visual balance.
- GoreeCloud identity recognition.

Every result remains pending until a named human reviewer records a finding separately under the V1.4.1 human-validation evidence protocol.

## Form-factor simulations

Desktop, mobile, tablet, TV, watch, and foldable buttons change only the visual review viewport. They are preparation aids and **are not physical-device evidence**. Actual form-factor qualification requires representative device/native-runtime review.

## Adapter-failure scenario

The `Simulate adapter failure` control intentionally throws inside the review-only signal adapter. The V1.4.1 Candidate runtime must contain that fault and force the `solid-accessible` fallback. The review surface exposes only bounded runtime status; the synthetic error detail is not written into DOM review state.

## Review findings

Do not convert this page, screenshots, or a planning packet directly into an accepted record. After a real review:

1. Record the reviewer identity and role.
2. Record the review timestamp with timezone.
3. Record the exact tested source revision, artifact, and build identifier.
4. Record the actual platform, OS/runtime, device/environment, display, inputs, and assistive technologies used.
5. Record each human finding, limitations, and supporting evidence references.
6. Author those observations in the separate `glaze-v1.4.1-human-validation` record format.
7. Leave anything not actually reviewed as `pending`.

If implementation changes after review, promotion-critical findings must be repeated on the final frozen release-candidate revision.

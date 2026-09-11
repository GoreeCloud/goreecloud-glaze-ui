# GLAZE UI V1.3 Supporting Evidence — 200% Large-Text Reflow

**Observed source revision:** `72ad63bf32d80420b25dc98bfd2def47bcc2a427`  
**Target:** GLAZE UI V1.3 / `1.3.0-candidate`  
**Date:** 2026-09-07  
**Evidence type:** Supporting human optical/runtime corroboration  
**Lifecycle effect:** None  
**Qualification status:** `in_progress`; this record is not an accepted Candidate workstream record.

## Session configuration

- Browser: Firefox Responsive Design Mode
- Emulated viewport: `390 x 844`
- DPR: `1`
- Page: `reference/v1.3/signature-components-and-compositions.html`
- Text-scale probe: `document.documentElement.style.fontSize = '200%'`
- Same frozen source revision as the active V1.3 qualification round.

## Observed behavior

The 200% text-scale run visibly recomposed rather than clipping or preserving a compressed desktop composition:

- header and reference copy reflowed into the narrow column;
- Signature component specimens stacked vertically;
- GlzCapsule allowed its action to reflow rather than collide with text;
- GlzMorphCard copy wrapped within its durable container;
- GlzSmartRail remained contained and compact;
- GlzAuroraSurface retained readable semantic copy;
- GlzUniversalSearch kept scope, input, shortcut, and metadata inside the component container;
- Canonical composition scenes stacked into a single-column presentation;
- no gross horizontal page overflow was visible;
- no critical text clipping was observed in the supplied captures;
- interactive surfaces remained present rather than disappearing during reflow.

## Capture references

The qualification conversation supplied two PNG captures. Their immutable local-file digests at review time were:

1. Full-page large-text capture  
   - native file dimensions: `87 x 2048` pixels (export downscaled because of extreme page height)  
   - SHA-256: `3a8c0f0d8535fb99c0dbefc546d3908085079c190e72fcb7dbec419bd08301b1`

2. Browser/viewport capture showing the 390 x 844 Responsive Design Mode configuration and the Universal Search large-text reflow  
   - native file dimensions: `1548 x 1050` pixels  
   - SHA-256: `6190b109815d0795aa4d6b25262d95810a2f19b19f0fb31b66dfde61bfa4c178`

## Evidence-quality limitation

The full-page export was compressed to only 87 pixels wide by the browser capture path. It is useful for ruling out gross structural failure, but it is not sufficient by itself for fine optical inspection. The normal browser capture is independently inspectable for the Universal Search region and confirms correct local reflow.

The human optical large-text sub-gate therefore remains **provisional / reviewer disposition pending** until the human reviewer explicitly accepts the observed 200% presentation and, if desired for stronger packaging, supplies several normal viewport screenshots covering top, middle, and lower sections.

## Boundary

This supporting record does **not** establish manual assistive-technology acceptance, physical-device accessibility acceptance, native-platform parity, Candidate activation, Stable promotion, or consumer eligibility. Those remain governed separately by the V1.3 qualification matrix and schema.

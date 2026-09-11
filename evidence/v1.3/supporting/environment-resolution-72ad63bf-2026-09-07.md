# GLAZE UI V1.3 Supporting Evidence — Environment Resolution

**Disposition:** PASS — supporting sub-gate only  
**Observed source revision:** `72ad63bf32d80420b25dc98bfd2def47bcc2a427`  
**Qualification evidence branch:** `evidence/glaze-ui-v1.3-qualification-72ad63b`  
**Observed date:** 2026-09-07  
**Lifecycle effect:** None. This record does not activate Candidate, promote Stable, establish consumer eligibility, or satisfy any complete governed qualification workstream.

## Purpose

Preserve the manually observed environment-resolution result for the frozen GLAZE UI V1.3 Candidate-qualification source revision. This artifact supports later human, accessibility, physical-device, and platform qualification; it is not a replacement for those records.

## Test surface

Local reference page:

`/reference/v1.3/signature-components-and-compositions.html`

Resolver module exercised from the browser console:

`/js/glaze-v1.3-component-experience.candidate.mjs`

Signature component:

`GlzUniversalSearch`

Console probe:

```js
(async()=>{const m=await import('/js/glaze-v1.3-component-experience.candidate.mjs');console.table(['medium','workspace','farView'].map(environment=>{const r=m.resolveSignatureComponent('GlzUniversalSearch',{environment,destinationCount:3,inputModality:environment==='farView'?'directional':'keyboard'});return{environment:r.environment,navigation:r.shell.navigation.presentation,search:r.presentation.presentation,minTarget:r.minimumInteractiveTargetPx}}))})()
```

## Observed matrix

| Environment | Navigation presentation | Search presentation | Minimum target |
| --- | --- | --- | ---: |
| `medium` | `navigation-rail` | `overlay-panel` | 48 px |
| `workspace` | `persistent-sidebar-plus-toolbar` | `command-overlay` | 48 px |
| `farView` | `directional-focus-navigation` | `focused-overlay` | 56 px |

All three rows matched the frozen V1.3 environment contract. In particular, `farView` resolved to directional-focus navigation and enforced the governed 56 px minimum-interactive-target floor.

## Screenshot provenance

The operator supplied one browser-console screenshot showing the complete three-row table and the local V1.3 reference page. The received PNG was 1548×1050 pixels, 164791 bytes, with SHA-256:

`de1c445f6ba719ee45923a15f0fef9d37cbafb6425b4f92b9285ef637adbc22a`

The screenshot itself is not embedded in this Git repository by this record; the hash is retained only to bind this observation to the exact supplied capture if it is archived separately.

## Scope boundary

This PASS establishes only the environment-resolution supporting sub-gate for the frozen source revision. It does **not** by itself satisfy or partially relabel any complete governed workstream, including:

- `human-optical-and-icon-collision-qualification`;
- `manual-assistive-technology-qualification`;
- `physical-device-native-platform-qualification`;
- `physical-device-production-performance-qualification`;
- `native-personalization-adapter-qualification`; or
- `stable-activation-and-source-namespace-cleanup`.

Responsive screenshots and resolver output are supporting evidence only. Required human authority, real assistive-technology sessions, physical-device/OEM/compositor observations, production-performance measurements, native-adapter evidence, and later Stable cleanup/equivalence review remain fail-closed until performed and recorded under the governed V1.3 evidence schema.

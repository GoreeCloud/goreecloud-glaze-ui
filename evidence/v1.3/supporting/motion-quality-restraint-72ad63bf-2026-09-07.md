# GLAZE UI V1.3 Supporting Evidence — Motion Quality + Motion Restraint

**Observed source revision:** `72ad63bf32d80420b25dc98bfd2def47bcc2a427`  
**Qualification branch:** `evidence/glaze-ui-v1.3-qualification-72ad63b`  
**Date:** 2026-09-07  
**Authority:** Human reviewer, live browser observation  
**Scope:** Supporting human-optical evidence only; not assistive-technology, physical-device, performance, native-adapter, Candidate-activation, or Stable acceptance.

## Test basis

The frozen V1.3 candidate inherits the bounded V1.2 Stable motion layer. Relevant governed behavior includes:

- bounded effective durations from 80 ms through 480 ms;
- press feedback using a subtle `.98` scale transform;
- direct manipulation remaining immediate;
- reduced-motion mode removing MorphCard/Capsule transitions and transforms;
- other reduced-motion surfaces collapsing to immediate behavior or minimal 80 ms opacity-only transitions.

The reference page was exercised live in Firefox. The reviewer performed click-and-hold/release interaction on the Project brief MorphCard and the Capsule Open action in normal motion mode, then repeated the same interactions after enabling `data-mode="reduced-motion"`.

On 2026-09-07 the reviewer explicitly reconfirmed the live result as **Motion PASS** while viewing the frozen V1.3 Signature Components + Composition Reference Suite. A full-page capture supplied with that attestation has SHA-256 fingerprint:

`d18e9a2c8c8240618d6907279b9a04a15a37f63be55d274a144a38ca1235260b`

The capture is supporting provenance for the observed page/revision context; motion acceptance itself is based on the reviewer's live interaction rather than a static image.

## Human disposition

**PASS**

The reviewer accepted that:

- normal press feedback was subtle, quick, and restrained;
- motion did not feel bouncy, dramatic, distracting, or layout-shifting;
- reduced-motion mode removed the nonessential scale/transition response cleanly;
- controls remained fully usable after reduced motion was enabled;
- motion remained presentation-only rather than semantic/state authority.

## Qualification mapping

This supporting evidence contributes to the human review of:

- `quality-22` Interaction Quality
- `quality-23` Tactility
- `quality-24` Motion Quality
- `quality-25` Motion Restraint
- `quality-26` Context Continuity
- `quality-53` Beauty Without Usability Loss

It does not by itself establish the complete 55-rule `human-optical-and-icon-collision-qualification` record.

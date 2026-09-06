# GLAZE UI V1.1

GLAZE UI V1.1 is GoreeCloud's current Stable shared visual and interaction design system. **Beauty is a requirement, not a regression risk.** Machine version: **1.1.1**.

## Core rule

**Solid where users read or make explicit critical decisions. Glazed where users interact with transient navigation, command, search, control, or feedback chrome.**

V1.1 preserves the V1 System Shell, 32-component catalog, semantic color, accessibility, material, performance, and native-mapping contracts while adding the approved Optical Refinement and **Deep Teal + Soft Amber** atmospheric system.

The atmosphere is intentionally subordinate: neutral structure remains dominant; protected semantic meaning, focus, accessibility, and required boundaries always resolve first. Environmental Color Memory remains optional and is not required by the first Stable implementation.

## Stable maintenance — 1.1.1

V1.1.1 is the corrective Stable maintenance package for the V1.1 line. It repairs the inherited CSS import-closure defect discovered after the immutable `1.1.0` publication. It does **not** change the approved V1.1 visual design, token values, semantic authority, accessibility contract, component catalog, System Shell contract, or runtime behavior.

The human-approved visual baseline therefore remains `1.1.0`, while the current consumer package and conformance target are `1.1.1`. Downstream applications do not become conformant or production-eligible automatically; each consumer must explicitly migrate and produce fresh repository-local acceptance evidence.

The corrective source was independently requalified on exact merged `main` revision `1af31aa69a40e740cfcaaca7fd5eee340da98c22` by post-merge V1.1 source, source-pinned rendered-web, and Android handheld release-evidence workflow `34034770603` before this promotion source was prepared.

## Next upgrade track — V1.2 Frosted Neutral

The next Glaze UI upgrade is being developed around a new governing optical rule: **Neutral glass is the material. Color is an accent.**

The V1.2 Candidate shifts default glazed surfaces toward frosty white, pearl, clear-neutral, soft gray, and neutral graphite glass with stronger blur, translucency, specular edge light, and depth. Teal, green, aqua, amber, and other chromatic colors are removed from the default material substrate and remain available for intentional active, focus, selection, progress, semantic, icon, and branding treatments.

Candidate source:
- `GLAZE_UI_V1_2_CANDIDATE.md` — next-upgrade contract
- `tokens/glaze-v1.2-frosted-neutral.candidate.json` — machine-readable material tokens
- `css/glaze-v1.2.0-candidate.css` — preview entrypoint layered over V1.1.1 Stable
- `reference/v1.2/frosted-neutral.html` — frosted-neutral visual reference
- `scripts/validate_glaze_v1_2_candidate.py` — fail-closed Candidate validator

V1.2 uses the corrected `1.1.1` package as its Stable inheritance point while retaining `1.1.0` as the unchanged approved V1.1 visual provenance. V1.2 remains Candidate until its governed visual, accessibility, performance, regression, and promotion gates pass. It does not automatically migrate downstream GoreeCloud applications.

## Stable evidence

Project-owner optical approval for the V1.1 appearance was recorded on 2026-09-03. Exact release-candidate revision `b37538f6748d95680ca5f6fe4a5e412a38ef87a7` reproduced the five approved web reference PNG hashes and passed fresh Android handheld emulator acceptance for Light/48dp, Dark + Reduced Transparency/48dp, and Deep Dark + 200% text + Touch Assistance/56dp in release-evidence workflow `33750604928`.

The import-closure correction was subsequently qualified against exact merged source and fresh web/Android evidence in workflow `34034770603`. The maintenance package preserves the original human-approved visual baseline rather than creating a new visual approval by automation.

Current source authority:
- `VERSION` — `1.1.1`
- `GLAZE_UI_V1_1.md` — official V1.1 visual/interaction contract
- `registry/lifecycle.json` — lifecycle and current-package authority
- `css/glaze-v1.1.1.css` — Stable maintenance web entrypoint
- `js/glaze-v1.1.1.mjs` — Stable maintenance runtime entrypoint
- `contracts/v1.1/patch-1.1.1.json` — maintenance release contract
- `contracts/v1.1/optical-refinement.json` — unchanged Stable optical contract
- `tokens/glaze-v1.1-atmosphere.json` — unchanged Stable atmosphere tokens
- `contracts/regression/visual-baselines-v1.json` — approved `1.1.0` visual baseline authority
- `acceptance/v1.1.1-stable.md` — maintenance Stable acceptance boundary

The V1.0 contract, immutable V1.1.0 package, and candidate/RC records remain historical audit evidence, not current consumer targets. No downstream GoreeCloud application auto-upgrades or gains production eligibility by declaration.

Glaze Motion remains separately Experimental.

## License

MIT. GoreeCloud branding and product identity remain subject to applicable project policies.

# GLAZE UI V1.2

GLAZE UI V1.2 is GoreeCloud's current Stable shared visual and interaction design system. **Beauty is a requirement, not a regression risk.** Machine version: **1.2.0**.

## Core rules

**Neutral glass is the material. Color is an accent.**

**Solid where users read or make explicit critical decisions. Glazed where users interact with transient navigation, command, search, control, or feedback chrome.**

V1.2 promotes the Frosted Neutral + Living Frosted system: Clear/Balanced/Dense clarity, adaptive optical response, Living Glaze interaction states, the inherited 32-component catalog and System Shell, adaptive navigation, responsive/form-factor composition, Personalization interfaces, accessibility precedence, and Tier 3 → Tier 0 graceful degradation.

## Stable source authority

- `VERSION` — `1.2.0`
- `GLAZE_UI_V1_2.md` — official Stable contract
- `registry/lifecycle.json` — lifecycle authority
- `css/glaze-v1.2.0.css` — Stable web entrypoint
- `js/glaze-v1.2.0.mjs` — Stable runtime entrypoint
- `tokens/glaze-v1.json` — current Stable V1 token manifest
- `acceptance/v1.2-stable.md` — V1.2 Stable acceptance/scope record
- `consumers/registry.json` — current consumer target and adoption state

The promoted V1.2 source keeps historical `.candidate` filenames internally where changing those names/selectors at release time would alter or unnecessarily churn proven rendering behavior. Those filenames are provenance only; they do not make the current lifecycle Candidate.

## V1.3 follow-up

On 2026-09-06 the GoreeCloud project owner moved the remaining V1.2 qualification blockers to V1.3. Human/manual/physical qualification that was not completed is **not** relabeled as passed V1.2 evidence. The carry-forward list is recorded in `acceptance/v1.3-deferred-qualification.md` and `contracts/v1.3/deferred-qualification.plan.json`.

## Consumer boundary

No downstream GoreeCloud application auto-upgrades or becomes production-eligible because V1.2 is Stable. Every applicable consumer must explicitly migrate to `1.2.0` and produce fresh repository-local evidence for its actual platform, accessibility, performance, and product acceptance boundary.

GLAZE UI V1.1 / `1.1.0` remains preserved as the prior known-good Stable rollback anchor. Glaze Motion remains separately Experimental unless explicitly incorporated by a Stable contract.

## License

MIT. GoreeCloud branding and product identity remain subject to applicable project policies.

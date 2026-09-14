# GLAZE UI V1.4.1 — Human Validation & Optical Hardening

**Lifecycle:** Planned follow-up  
**Baseline:** GLAZE UI V1.4 / `1.4.0` Stable  
**Purpose:** Human validation, human verification, physical-device qualification, subjective optical polish, additive optical-runtime hardening, and fail-closed review preparation.

V1.4.1 is the explicit home for human-dependent validation deferred from the V1.4.0 Stable release by owner direction. Deferral does not mean these checks passed; it means they are non-blocking for V1.4.0 lifecycle activation and remain open work for this patch track.

V1.4.1 may also contain additive runtime hardening that preserves the accepted V1.4.0 Stable source unchanged. Machine-verifiable hardening does not replace or satisfy the human-dependent work below.

## Required human-validation work

- Review Content-Aware Frost over calm, noisy, bright, dark, photographic, video, and high-motion backgrounds.
- Review Semantic Blur Protection around text, icons, faces, labels, controls, and critical status regions.
- Review environment tint and light warmth across light, dark, deep-dark, dawn, day, dusk, and night contexts.
- Review chromatic depth separation for base, raised, overlay, and modal surfaces.
- Review environmental color memory for subtlety, identity preservation, and unwanted color contamination.
- Validate Reduced Transparency, Increased Contrast, Forced Colors, Reduced Motion, large text, RTL, keyboard, touch, pointer, switch, voice, and supported assistive technologies where applicable.
- Validate supported Android/OEM, Linux compositor/window, desktop, mobile, tablet, TV, watch, foldable, and other claimed form-factor behavior on representative physical devices.
- Measure representative real-device performance, thermal/power behavior, animation smoothness, and degradation behavior.
- Perform subjective polish review for glass quality, depth, warmth, animation/touch feel, visual balance, and GoreeCloud identity recognition.

## Optical runtime hardening

V1.4.0 already bounds malformed optical values after they are returned by a consumer context adapter. V1.4.1 additionally hardens the adapter invocation boundary itself.

The V1.4.1 Candidate runtime must treat a thrown `signalAdapter.resolve()` exception as a failure to establish trusted contextual signal state. It must not propagate that adapter exception through ordinary Glaze optical resolution or application, and it must not silently retain decorative adaptive optics as though the context were trustworthy.

The required failure behavior is:

- collapse to the existing V1.4 `solid-accessible` optical mode;
- force the Reduced Transparency and Forced Colors accessibility path after consumer overrides are composed;
- disable blur and decorative memory tint;
- prevent caller overrides from re-enabling decorative optics for that failed adapter resolution;
- expose only the bounded adapter status `failed-safe` to applied DOM state, never raw error messages, stacks, or adapter details;
- permit an optional local `onAdapterError` observer for consumer diagnostics without requiring telemetry or remote reporting;
- swallow observer failures so a diagnostic callback cannot defeat the accessibility fallback;
- leave V1.4.0 Stable source and runtime entrypoints byte-for-byte/Git-blob unchanged.

The runtime hardening authority is:

- `contracts/v1.4.1/optical-runtime-hardening.contract.json` — machine contract, Stable blob bindings, and fail-safe rules.
- `js/glaze-v1.4.1-optical-engine.candidate.mjs` — additive hardened Candidate wrapper around the V1.4.0 resolver/apply authority.
- `js/glaze-v1.4.1.candidate.mjs` — additive Candidate runtime entrypoint inheriting V1.4.0.
- `scripts/verify_glaze_v1_4_1_optical_runtime.mjs` — machine verifier for adapter success, malformed values, thrown adapter faults, override resistance, observer faults, DOM-status privacy, Stable blob immutability, and non-claim boundaries.

The V1.4.1 Candidate runtime is local and deterministic. It does not require telemetry, analytics, camera access, or remote context. Consumers remain responsible for the privacy and security authority of the signals they provide. The optional error observer is not a telemetry requirement and must not be interpreted as permission for remote reporting.

Machine verification command:

```sh
node scripts/verify_glaze_v1_4_1_optical_runtime.mjs
```

Passing this runtime verifier proves only the bounded machine behavior described by the contract. It does not establish human optical quality, physical-device behavior, assistive-technology acceptance, real-device performance, or V1.4.1 release readiness.

## Human review packet preparation

Human review preparation must be convenient without allowing tooling to impersonate the reviewer or pre-authorize acceptance. V1.4.1 therefore defines a separate **review packet** format for preparing an exact revision, build, environment, and the canonical 34-check review matrix before a person begins testing.

A review packet is deliberately **not** a human-validation evidence record. It uses a different `packetType`, declares `authority: pre-review-planning-only`, contains no human reviewer or reviewer role, contains no review timestamp, contains no human evidence sessions, forces every check to `pending`, starts with no findings or evidence references, and forces `promotionEligible: false`.

The review-packet authority is:

- `schemas/v1.4.1-human-review-packet.schema.json` — planning-only structural schema with exactly 34 pending checks.
- `scripts/generate_glaze_v1_4_1_review_packet.mjs` — fail-closed generator for exact revision/build/environment packets.
- `scripts/verify_glaze_v1_4_1_review_packet.mjs` — contract/schema parity and packet verifier that also proves the real human-evidence verifier rejects planning packets.

Generate a packet for a real review environment before review begins:

```sh
node scripts/generate_glaze_v1_4_1_review_packet.mjs \
  --source-revision <40-character-tested-revision> \
  --artifact <artifact-or-build-path> \
  --build-id <build-identifier> \
  --platform <platform> \
  --os-version <os-version> \
  --device <device-or-environment> \
  --form-factor <form-factor> \
  --display <display-context> \
  --input-modality <input> \
  --assistive-technology <assistive-technology> \
  --output review-packets/<packet-name>.json
```

`--input-modality` and `--assistive-technology` may be repeated. The generator creates missing output directories and refuses to overwrite an existing packet unless `--force` is explicitly supplied.

Verify a prepared packet before giving it to a reviewer:

```sh
node scripts/verify_glaze_v1_4_1_review_packet.mjs \
  --packet review-packets/<packet-name>.json
```

The packet verifier checks canonical contract/schema parity, exact 34-check coverage, pending-only state, empty generated findings/evidence, absence of human-authority fields, and `promotionEligible: false`. It then invokes the actual V1.4.1 human-evidence verifier and requires that verifier to reject the planning packet as evidence.

After real review, do **not** simply relabel the packet or change `promotionEligible`. Human-authorized findings must be recorded in the separate human-validation record format with the real reviewer identity, role, review timestamp, tested build/revision, environment, findings, limitations, and evidence references required by the human-evidence protocol.

## Evidence rule

Every completed human item must identify the tested build/revision, device or environment, reviewer, scope, result, and any accepted limitation. Automated evidence may support a review but must not be relabeled as human evidence.

V1.4.1 uses a structured multi-session evidence protocol so one record can combine review sessions across Android, Linux, desktop, mobile, tablet, TV, watch, foldable, accessibility, and performance environments without flattening them into one misleading global pass state.

The human-evidence protocol authority is:

- `contracts/v1.4.1/human-validation.contract.json` — canonical required-check matrix and fail-closed rules.
- `schemas/v1.4.1-human-validation-record.schema.json` — Draft 2020-12 structural schema for editor/tool validation; schema validity alone is never human acceptance.
- `acceptance/v1.4.1-human-validation.template.json` — deliberately pending template; never acceptance evidence by itself.
- `scripts/verify_glaze_v1_4_1_human_validation_schema.mjs` — contract/schema/template parity verifier.
- `scripts/verify_glaze_v1_4_1_human_validation.mjs` — machine validation of evidence authority, coverage, revision binding, and promotion eligibility.

Each human review session must identify the exact tested source revision, build/artifact identity, timestamp with timezone, named reviewer and role, platform, OS version, device/environment, form factor, display context, relevant input modalities, assistive technologies, findings, limitations, and evidence references.

A check may be marked `not_applicable` only with an explicit rationale. `pending`, `blocked`, or `fail` cannot satisfy promotion. A claimed `pass` or `fail` requires at least one evidence reference. Machine-generated supporting artifacts can be referenced, but the record itself must remain human-authorized.

### Verification

Validate the schema/contract parity, protocol, and synthetic negative tests without claiming human acceptance:

```sh
node scripts/verify_glaze_v1_4_1_human_validation_schema.mjs
node scripts/verify_glaze_v1_4_1_human_validation.mjs --source-only
node scripts/verify_glaze_v1_4_1_human_validation.mjs --self-test
```

Validate a real record without asserting patch promotion:

```sh
node scripts/verify_glaze_v1_4_1_human_validation.mjs --record path/to/human-record.json
```

Run the fail-closed promotion gate only when a real record exists and the exact reviewed implementation revision is known:

```sh
node scripts/verify_glaze_v1_4_1_human_validation.mjs \
  --record path/to/human-record.json \
  --promotion \
  --expected-revision <40-character-reviewed-revision>
```

The schema validator and verifier's synthetic self-test are protocol testing only. They are never human evidence, never physical-device evidence, and never V1.4.1 acceptance.

## Patch acceptance

V1.4.1 may be promoted only after its claimed human/manual/physical-device evidence is actually recorded and any release-blocking findings are resolved or explicitly scoped out of the supported claim. V1.4.1 must not retroactively rewrite V1.4.0 evidence.

Promotion additionally requires the structured record to cover every canonical required check, contain no unresolved exceptions, contain no `pending`, `blocked`, or `fail` results, explicitly declare an accepted decision, explicitly declare promotion eligibility, and bind every contributing review session to the exact revision supplied to the promotion gate.

Machine runtime hardening may remove release-blocking implementation defects, and review-packet tooling may prepare real review work, but neither can satisfy or waive human-authority checks. V1.4.1 remains non-promotable until both its claimed machine hardening and its required real human evidence are valid for the governed release revision.

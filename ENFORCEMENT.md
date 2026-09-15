# GLAZE UI V1.4 — Enforcement

The current Glaze UI enforcement and consumer-conformance target is **GLAZE UI V1.4** (`1.4.0`). `registry/lifecycle.json` and `VERSION` are the current lifecycle authorities. GLAZE UI V1.3 (`1.3.0`) remains the immediately preceding known-good Stable rollback baseline and does not override the current target.

Enforcement fails closed when required V1 evidence is absent, stale, or bound to a different revision. Consumers must not claim conformance from copied tokens, renamed assets, screenshots alone, a platform declaration, or the shared V1.4 Stable promotion itself. Required checks include exact-revision contract validation, accessibility, supported form factors, rendered/native evidence where applicable, performance budgets, and product-specific production acceptance.

V1.4.1 is a governed follow-up to the current Stable release. Machine implementation and CI may prepare or verify candidate behavior, but V1.4.1 human/manual/physical evidence remains separate and must not be converted into Stable, consumer-conformance, or production claims until its exact-revision promotion requirements are actually satisfied.

Historical V1.0–V1.3 release, Candidate, and qualification records remain provenance and rollback evidence. They do not override live `VERSION` / lifecycle authority or manufacture current acceptance.

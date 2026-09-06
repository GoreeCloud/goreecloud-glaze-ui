# GLAZE UI V1.2 — Enforcement

The current Glaze UI enforcement and consumer-conformance target is **GLAZE UI V1.2** (`1.2.0`). `registry/lifecycle.json` and `VERSION` are the current lifecycle authorities. GLAZE UI V1.1 (`1.1.0`) remains the previous known-good Stable rollback baseline and does not override the current target.

Enforcement fails closed when required V1 evidence is absent, stale, or bound to a different revision. Consumers must not claim conformance from copied tokens, renamed assets, screenshots alone, a platform declaration, or the shared V1.2 Stable promotion itself. Required checks include exact-revision contract validation, accessibility, supported form factors, rendered/native evidence where applicable, performance budgets, and product-specific production acceptance.

The V1.0 reset established the V1 namespace and remains historical baseline evidence. The V1.2 Candidate source lineage is preserved for audit and promoted-source validation, but live V1.2 lifecycle authority is Stable `1.2.0` with no active V1.2 Candidate. The remaining external/manual/physical qualification work was explicitly moved to V1.3 and is not represented as passed V1.2 evidence.

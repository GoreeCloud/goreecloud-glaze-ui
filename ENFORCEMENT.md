# GLAZE UI V1.1 — Enforcement

The sole current Glaze UI enforcement and consumer-conformance target is **GLAZE UI V1.1** (`1.1.0`). `registry/lifecycle.json` and `VERSION` are the current lifecycle authorities. Enforcement fails closed when required V1 evidence is absent, stale, or bound to a different revision.

Consumers must not claim conformance from copied tokens, renamed assets, screenshots alone, or a platform declaration. Required checks include exact-revision contract validation, accessibility, supported form factors, rendered/native evidence where applicable, performance budgets, and product-specific production acceptance.

The V1.0 reset established the V1 namespace and remains historical baseline evidence; it does not override the later governed V1.1 Stable promotion. V1.2 remains a non-consumer-eligible Candidate until separately promoted through governed release gates.

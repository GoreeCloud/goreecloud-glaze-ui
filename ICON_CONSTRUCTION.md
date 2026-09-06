# GLAZE UI V1.0-Origin — Icon Grid, Geometry, Materials, and Construction Contract

**Contract origin:** Official V1.0 reset baseline; inherited by later V1 releases unless superseded.  
**Current Stable product authority:** GLAZE UI V1.2 / `1.2.0`.

`tokens/icon-construction.json` retains an internal icon-construction contract revision and baseline of `1.5.0`. That value is a subsystem-contract revision only. It does not define another Glaze UI product release, consumer target, or production-acceptance state. Product lifecycle authority remains separate in `registry/lifecycle.json` and `VERSION`.

## Purpose

This contract defines how application and service identity assets are constructed, simplified, packaged, validated, and described for tooling across the V1 generation. It originated in GLAZE UI V1.0 and remains inherited by the current V1.2 Stable product unless a later governed contract explicitly supersedes it.

## Master canvas and protected zones

Primary application identity source artwork uses a normalized **1024 × 1024** master canvas with optical origin **512 × 512**.

The default construction zones are percentage-based references rather than mandatory clipping masks:

- **Canvas Boundary** — 100% of the coordinate space.
- **Presentation Zone** — approximately 90%, containing the outer presentation container and controlled optical overshoot.
- **Optical Safe Zone** — approximately 76%, containing most important identity geometry.
- **Core Identity Zone** — approximately 60%, containing characteristics that must survive Compact and Micro presentation.

Optical correction and controlled overshoot are permitted where needed for perceptual balance.

## Keyline families and curvature

The master grid supports circular, continuous-square, vertical, horizontal, compact-object, and freeform keyline families. Keylines are visual-weight references, not mandatory masks.

The V1 construction grammar uses four conceptual curvature levels: **Subtle**, **Standard**, **Expressive**, and **Full**. Curvature should transition continuously rather than defaulting to unrelated arbitrary radii.

## Material hierarchy and application layers

Material overlap uses an explicit order: background, structural, identity, then highlight material. Multiple equally prominent translucent layers are avoided because they create ambiguity.

Application construction proceeds through foundation, material, identity, detail, and light. Recognition must survive removal of gradients, translucency, lighting, shadows, and secondary detail.

## Identity Lock

Every major application and service identity requires an Identity Lock recording primary geometry, silhouette, orientation, distinctive negative space, characteristic proportions, and essential color relationships. Adaptive presentation may evolve around the lock; recognition properties must not drift casually across themes, sizes, accessibility modes, or redesigns.

## Optical representations

Every major application and service identity supports purpose-built **Display**, **Standard**, **Compact**, and **Micro** representations. Scaling Display artwork down is not an acceptable substitute for Compact or Micro construction.

The reduction sequence is:

**Material richness → structural clarity → silhouette → identity**

Negative space and stroke strength must remain legible through that reduction. Micro representations should prefer simplified filled geometry over fragile detail when that improves recognition.

## Semantic states and badges

Identity remains stable when state changes. Selection prefers surrounding surface treatment. Disabled and unavailable remain distinct. Progress remains separate from identity, and notification quantity remains distinct from semantic badges.

Success, information, warning, danger, privacy, security, syncing, offline, paused, restricted, managed, unavailable, and related states use standardized semantic treatment rather than recoloring the base identity into another product.

## Motion grammar

Icon motion is classified as state-transition, progress, activity, attention, or confirmation. Persistent motion is not used merely because animation is available, and Reduced Motion must preserve understandable state changes.

## Validation matrix

Important icons are reviewed in launcher-grid comparison, squint/blur silhouette tests, grayscale, Micro representation, badge collision, background stress, light/dark appearance, high contrast, Reduced Transparency, Reduced Motion, color-vision accommodation, and monochrome presentation.

An icon that succeeds alone but disrupts the system grid is incomplete.

## Structured icon package

A production icon is a structured identity asset rather than one bitmap. A package may include authoritative source artwork, Display/Standard/Compact/Micro representations, monochrome identity, accessibility behavior, identity colors, material metadata, Identity Lock metadata, badge clearance, adaptive appearance, and optional motion definitions.

Each package uses the machine-readable manifest defined by `schemas/icon-manifest.schema.json`. `examples/icon-manifest.example.json` is a schema example only and does not certify current GoreeCloud artwork.

Source identity is separated from final rendering so future display technologies may evolve presentation without replacing semantic structure. A Glaze UI icon is therefore a **responsive visual identity asset** rather than a static bitmap.

## Authoring and Planned tooling

Glaze UI does **not** plan a dedicated Icon Studio application. Ordinary professional design tools may be used with repository-controlled source assets and reproducible validation or generation scripts.

Live environment preview, automatic production export, icon linting, and a searchable System Icon Registry may remain **Planned** capabilities where they provide clear value. Planned tooling must not be represented as implemented or required for authorship before it exists.

## V1 inheritance and acceptance boundary

This construction contract originated in the official GLAZE UI V1.0 reset baseline, was inherited by V1.1, and remains inherited by V1.2 where not superseded. The internal `1.5.0` icon-construction revision remains a subsystem revision and must not be interpreted as a Glaze UI product version. Machine-contract consistency does not certify rendered artwork or establish production Stable acceptance. Fresh exact-revision visual, accessibility, optical-size, platform, and package validation is required before production acceptance may be claimed.

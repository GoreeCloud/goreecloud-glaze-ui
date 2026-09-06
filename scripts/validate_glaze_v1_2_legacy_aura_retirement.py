#!/usr/bin/env python3
"""Fail closed if retired V1.1 teal/amber Aura values leak back into V1.2.

This gate proves token-level retirement only. It deliberately permits the inherited
V1.1 CSS variable names to survive as transparent compatibility neutralizers while
V1.2 remains layered on V1.1 Stable. Passing this gate does not establish RC, Stable,
human optical acceptance, native parity, production acceptance, or consumer conformance.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROSTED_TOKEN = ROOT / "tokens/glaze-v1.2-frosted-neutral.candidate.json"
OPTICAL_TOKEN = ROOT / "tokens/glaze-v1.2-optical-foundation.candidate.json"
MIGRATION = ROOT / "contracts/v1.2/migration.candidate.json"
MIGRATION_DOC = ROOT / "MIGRATION_V1_1_TO_V1_2.md"
ENTRYPOINT = ROOT / "css/glaze-v1.2.0-candidate.css"
CSS_DIR = ROOT / "css"
CI = ROOT / ".github/workflows/ci.yml"

LEGACY_FIELDS = (
    "lightAuraMaxAlpha",
    "darkAuraMaxAlpha",
    "deepDarkAuraMaxAlpha",
)
LEGACY_ASSIGNMENT = re.compile(
    r"--glz11-aura-(?:teal|amber)-max\s*:\s*([^;]+);",
    flags=re.IGNORECASE,
)


def req(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"GLAZE UI V1.2 legacy Aura retirement validation failed: {message}")


def text(path: Path) -> str:
    req(path.is_file(), f"missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def obj(path: Path) -> dict:
    value = json.loads(text(path))
    req(isinstance(value, dict), f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def main() -> None:
    frosted = obj(FROSTED_TOKEN)
    optical = obj(OPTICAL_TOKEN)
    migration = obj(MIGRATION)
    migration_doc = text(MIGRATION_DOC)
    entrypoint = text(ENTRYPOINT)
    ci = text(CI)

    req(frosted.get("version") == "1.2.0-candidate", "Frosted Neutral version drifted")
    req(frosted.get("lifecycle") == "candidate", "Frosted Neutral lifecycle must remain Candidate")
    req(frosted.get("stableBaseline") == "1.1.0", "Stable baseline must remain 1.1.0")
    req(frosted.get("currentStableToken") is False, "V1.2 token must not claim Stable authority")

    atmosphere = frosted.get("atmosphere", {})
    req(isinstance(atmosphere, dict), "Frosted Neutral atmosphere must be an object")
    for field in LEGACY_FIELDS:
        req(field not in atmosphere, f"retired legacy Aura field returned: {field}")
    atmosphere_text = json.dumps(atmosphere, sort_keys=True).lower()
    req("teal" not in atmosphere_text, "V1.2 Frosted Neutral atmosphere must not carry teal Aura values")
    req("amber" not in atmosphere_text, "V1.2 Frosted Neutral atmosphere must not carry amber Aura values")
    req(
        atmosphere.get("auraPaletteAuthority") == "tokens/glaze-v1.2-optical-foundation.candidate.json",
        "Frosted Neutral must delegate Aura palette authority to the V1.2 optical foundation",
    )
    req(
        atmosphere.get("legacyV11AuraCompatibility") == "retired-to-frost-ice",
        "legacy V1.1 Aura compatibility must remain retired to Frost/Ice",
    )

    aura_families = optical.get("auraFamilies", {})
    req(
        set(aura_families) == {"frostAura", "iceAura", "crystalAura", "contentAura"},
        "V1.2 Aura authority must remain exactly Frost/Ice/Crystal/Content",
    )
    aura_policy = optical.get("auraPolicy", {})
    req(aura_policy.get("defaultAtmosphere") == "ice-blue", "V1.2 default atmosphere must remain Ice Blue")
    req(aura_policy.get("tealDefaultAtmosphereAllowed") is False, "teal may not become the V1.2 default atmosphere")
    req(aura_policy.get("legacyAuraPromotionRequirement") == "retire-or-map-to-frost-ice-before-rc", "legacy Aura RC invariant drifted")

    debt = migration.get("knownAlignmentDebt", [])
    req(isinstance(debt, list), "knownAlignmentDebt must be an array")
    legacy_debt = next(
        (item for item in debt if isinstance(item, dict) and item.get("id") == "legacy-v11-aura-fields"),
        None,
    )
    req(legacy_debt is not None, "legacy Aura debt record is missing")
    assert legacy_debt is not None
    req(legacy_debt.get("state") == "resolved-candidate", "legacy Aura debt must remain resolved at Candidate scope")
    req(
        migration.get("currentCandidateEvidence", {}).get("legacyAuraTokenRetirement") == "implemented-candidate",
        "migration contract must record Candidate token-retirement evidence",
    )

    assignments: list[tuple[str, str]] = []
    for css_path in sorted(CSS_DIR.glob("glaze-v1.2-*.candidate.css")):
        css = text(css_path)
        for match in LEGACY_ASSIGNMENT.finditer(css):
            assignments.append((css_path.name, match.group(1).strip()))
    req(assignments, "inherited V1.1 Aura variables are no longer explicitly neutralized")
    for filename, value in assignments:
        req(value.lower() == "transparent", f"{filename} assigns a retired V1.1 Aura variable to non-transparent value {value!r}")

    retirement_import = '@import url("./glaze-v1.2-legacy-aura-retirement.candidate.css")'
    optical_import = '@import url("./glaze-v1.2-optical.candidate.css")'
    accessibility_import = '@import url("./glaze-v1.2-accessibility.candidate.css")'
    for marker in (optical_import, retirement_import, accessibility_import):
        req(marker in entrypoint, f"Candidate entrypoint missing required import {marker}")
    req(
        entrypoint.index(optical_import) < entrypoint.index(retirement_import) < entrypoint.index(accessibility_import),
        "legacy Aura transparent neutralizer must follow optical roles and precede final accessibility authority",
    )

    req(
        "V1.2 no longer exposes teal/amber Aura alpha tokens" in migration_doc,
        "human-readable migration plan does not record token-level Aura retirement",
    )
    req(
        "[x] Legacy V1.1 atmosphere compatibility retired or governed." in migration_doc,
        "migration promotion checklist does not record the completed legacy Aura requirement",
    )
    req(
        "python scripts/validate_glaze_v1_2_legacy_aura_retirement.py" in ci,
        "CI must execute the legacy Aura retirement validator",
    )

    print("GLAZE UI V1.2 legacy Aura token retirement validation passed")
    print("V1.2 Aura authority: Frost / Ice / Crystal / Content")
    print(f"Transparent inherited V1.1 compatibility assignments: {len(assignments)}")
    print("Lifecycle authority unchanged: V1.1 / 1.1.0 Stable; V1.2 Candidate")


if __name__ == "__main__":
    main()

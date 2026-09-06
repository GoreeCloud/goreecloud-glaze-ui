#!/usr/bin/env python3
"""Validate the GLAZE UI V1.2 application-icon Ecosystem Wall review artifact."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/v1.2/application-icon-ecosystem-wall.candidate.json"
REFERENCE = ROOT / "reference/v1.2/application-icon-ecosystem-wall.html"
BRANDING_ROOT = ROOT / ".branding-sources/goreecloud-branding-assets"
EXPECTED_REPOSITORY = "GoreeCloud/goreecloud-branding-assets"
EXPECTED_REVISION = "f5afcac107971d9e01c5910ac1a1c6e4ca0c6543"
EXPECTED_CATALOG_BLOB = "b982ea371a25685950be0466725dc93c8eaef885"
EXPECTED_PRODUCT_COUNT = 38
EXPECTED_SCALES = [96, 56, 32]


class ValidationError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValidationError(message)


def load_json(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected object in {path.relative_to(ROOT)}")
    return value


def git_output(*args: str, cwd: Path) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True, stderr=subprocess.STDOUT).strip()


def validate_contract() -> dict[str, Any]:
    contract = load_json(CONTRACT)
    require(contract.get("schemaVersion") == 1, "Ecosystem Wall schema drifted")
    require(contract.get("id") == "glaze-v1.2-application-icon-ecosystem-wall-candidate", "Ecosystem Wall id drifted")
    require(contract.get("product") == "GLAZE UI", "Ecosystem Wall product drifted")
    require(contract.get("version") == "1.2.0-candidate", "Ecosystem Wall version drifted")
    require(contract.get("lifecycle") == "candidate", "Ecosystem Wall lifecycle drifted")
    require(contract.get("stableBaseline") == "1.1.0", "Stable baseline drifted")
    require(contract.get("consumerEligible") is False, "Ecosystem Wall became consumer eligible")
    require(contract.get("sceneId") == "application-icon-ecosystem-wall", "scene id drifted")
    require(contract.get("status") == "review-artifact-generated-human-review-pending", "review-artifact status drifted")

    source = contract.get("brandingSource", {})
    require(source.get("repository") == EXPECTED_REPOSITORY, "branding repository drifted")
    require(source.get("revision") == EXPECTED_REVISION, "branding revision drifted")
    require(re.fullmatch(r"[0-9a-f]{40}", str(source.get("revision") or "")) is not None, "branding revision is not immutable")
    require(source.get("catalogPath") == "catalog.json", "branding catalog path drifted")
    require(source.get("catalogGitBlob") == EXPECTED_CATALOG_BLOB, "branding catalog blob drifted")
    require(source.get("assetCollection") == "products", "asset collection drifted")
    require(source.get("expectedAssetCount") == EXPECTED_PRODUCT_COUNT, "expected application icon count drifted")
    require(source.get("canonicalAssetsOnly") is True, "canonical-only source rule weakened")
    require(source.get("referenceReviewRetrievalOnly") is True, "reference-only retrieval boundary weakened")
    require(source.get("consumerRuntimeDependency") is False, "reference retrieval became a consumer runtime dependency")

    scales = contract.get("scales")
    require(isinstance(scales, list), "review scales must be an array")
    require([scale.get("sizePx") for scale in scales if isinstance(scale, dict)] == EXPECTED_SCALES, "multi-scale review sizes drifted")

    rules = contract.get("rules", {})
    for key in (
        "sharedDnaWithoutSharedIdentity",
        "canonicalAssetsOnly",
        "localProductRedesignProhibited",
        "humanCollisionReviewFinalAuthority",
        "wallGenerationMayNotPromoteCandidate",
        "wallGenerationMayNotEstablishStable",
        "wallGenerationMayNotEstablishConsumerConformance",
    ):
        require(rules.get(key) is True, f"Ecosystem Wall rule weakened: {key}")
    require(rules.get("brandingAuthorityTransferred") is False, "branding authority transferred")
    require(rules.get("automatedCollisionAcceptance") is False, "automation became collision acceptance authority")

    human = contract.get("humanReview", {})
    require(human == {
        "required": True,
        "status": "pending",
        "finalAuthority": True,
        "acceptedRevision": None,
        "reviewedAt": None,
    }, "human-review boundary drifted")

    implementation = contract.get("implementation", {})
    require(implementation == {
        "reference": "reference/v1.2/application-icon-ecosystem-wall.html",
        "validator": "scripts/validate_glaze_v1_2_application_icon_ecosystem_wall.py",
        "workflow": ".github/workflows/glaze-v1.2-application-icon-ecosystem-wall.yml",
    }, "Ecosystem Wall implementation binding drifted")

    boundary = contract.get("evidenceBoundary", {})
    for marker in (
        "multi-scale-application-icon-review-artifact",
        "immutable-branding-source-pin",
        "canonical-catalog-and-asset-blob-validation",
        "human-review-authority-preserved",
    ):
        require(marker in boundary.get("established", []), f"established evidence marker missing: {marker}")
    for marker in (
        "human-collision-review",
        "human-optical-acceptance",
        "accepted-application-icon-ecosystem-wall-reference-scene",
        "release-candidate",
        "stable",
        "consumer-conformance",
    ):
        require(marker in boundary.get("notEstablished", []), f"fail-closed evidence marker missing: {marker}")
    return contract


def validate_branding_source(contract: dict[str, Any]) -> list[dict[str, Any]]:
    require(BRANDING_ROOT.is_dir(), "exact branding source checkout is missing")
    actual_revision = git_output("rev-parse", "HEAD", cwd=BRANDING_ROOT)
    require(actual_revision == EXPECTED_REVISION, "branding checkout does not match the reviewed immutable revision")

    catalog_path = BRANDING_ROOT / contract["brandingSource"]["catalogPath"]
    catalog = load_json(catalog_path)
    require(catalog.get("canonical_repository") == EXPECTED_REPOSITORY, "catalog canonical repository drifted")
    actual_catalog_blob = git_output("hash-object", str(catalog_path), cwd=BRANDING_ROOT)
    require(actual_catalog_blob == EXPECTED_CATALOG_BLOB, "catalog content does not match pinned Git blob")

    products = catalog.get("products")
    require(isinstance(products, list), "canonical product catalog is not an array")
    require(len(products) == EXPECTED_PRODUCT_COUNT, f"expected {EXPECTED_PRODUCT_COUNT} canonical products, found {len(products)}")

    ids: set[str] = set()
    names: set[str] = set()
    for product in products:
        require(isinstance(product, dict), "canonical product entry is not an object")
        product_id = product.get("id")
        name = product.get("name")
        asset = product.get("canonical_asset")
        blob = product.get("git_blob")
        require(isinstance(product_id, str) and product_id, "canonical product id missing")
        require(isinstance(name, str) and name, f"{product_id}: canonical product name missing")
        require(product_id not in ids, f"duplicate product id: {product_id}")
        require(name not in names, f"duplicate product name: {name}")
        ids.add(product_id)
        names.add(name)
        require(asset == f"products/{product_id}/app-icon.svg", f"{product_id}: canonical application icon path drifted")
        require(isinstance(blob, str) and re.fullmatch(r"[0-9a-f]{40}", blob) is not None, f"{product_id}: canonical asset blob is not immutable")
        asset_path = BRANDING_ROOT / asset
        require(asset_path.is_file(), f"{product_id}: canonical application icon missing")
        actual_blob = git_output("hash-object", str(asset_path), cwd=BRANDING_ROOT)
        require(actual_blob == blob, f"{product_id}: canonical application icon blob mismatch")
    return products


def validate_reference(products: list[dict[str, Any]]) -> None:
    require(REFERENCE.is_file(), f"missing {REFERENCE.relative_to(ROOT)}")
    text = REFERENCE.read_text(encoding="utf-8")
    for marker in (
        'data-ecosystem-wall="application-icons"',
        "Application Icon Ecosystem Wall",
        EXPECTED_REPOSITORY,
        EXPECTED_REVISION,
        "EXPECTED_PRODUCT_COUNT = 38",
        "size:96",
        "size:56",
        "size:32",
        "raw.githubusercontent.com",
        "catalog.json",
        "no fallback artwork is substituted",
    ):
        require(marker in text, f"Ecosystem Wall reference marker missing: {marker}")
    require("human collision review remains final" in text.lower(), "Ecosystem Wall reference lost human collision-review authority")
    require("/main/" not in text, "Ecosystem Wall must not fetch mutable branding main")
    require("<svg" not in text.lower(), "Ecosystem Wall must not invent local replacement product artwork")
    require("data:image" not in text.lower(), "Ecosystem Wall must not hide ungoverned embedded product artwork")
    require(text.count("data-ecosystem-wall=\"application-icons\"") == 1, "Ecosystem Wall scene identity is ambiguous")
    require(len(products) == EXPECTED_PRODUCT_COUNT, "reference product count lost canonical catalog binding")


def main() -> int:
    try:
        contract = validate_contract()
        products = validate_branding_source(contract)
        validate_reference(products)
    except (ValidationError, json.JSONDecodeError, OSError, subprocess.CalledProcessError) as error:
        print(f"FAIL: {error}")
        return 1
    print(
        "PASS: V1.2 Application Icon Ecosystem Wall review artifact is multi-scale and bound to 38 canonical "
        f"branding assets at {EXPECTED_REVISION}; human collision/optical review remains pending and authoritative."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

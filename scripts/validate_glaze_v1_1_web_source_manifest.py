#!/usr/bin/env python3
"""Validate the immutable GLAZE UI V1.1 Stable web source manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "releases" / "1.1.0-web-source.json"
EXPECTED_RELEASE_COMMIT = "15cc76d2bcd4065552dc31c77145b63f34d9e7b2"
EXPECTED_RELEASE_TREE = "52eb8207272498db227c984d2398e1242b659393"
EXPECTED_ENTRYPOINT = "css/glaze-v1.1.0.css"
EXPECTED_FILES = {
    "css/glaze-v1.1.0.css": "c689e8e58cefc49f931862996a1e0e871497fe88",
    "css/glaze-v1.0.0.css": "eca2209c5d678830f92907b4d44ea6cc5b1c8536",
    "css/glaze-v1.1.css": "aa0250f01151f17cd3c77e9a67544c6af4b5aa32",
    "css/glaze-v1.1-appearance.css": "c4e10e043d537c68f1e4a5f97bdb8b6f0d371dce",
    "css/glaze-v1.foundation.css": "b01051203831ce011c08f37b79f2e2032d34d0c8",
    "css/glaze-v1.components.css": "f74d5d4a4dd3ae22354812260e06a042d3928507",
    "css/glaze-v1.components.adaptive.css": "e174ea4923ec1ac6e1eb52d7ee33c14f2f77d5ca",
    "css/glaze-v1.components.runtime.css": "a89356172d74b66c62cfda198ae827fe9b71c520",
    "css/glaze-v1.structure.css": "9781c3e162edbac9fce67b93fd3287fdacbcd504",
    "css/glaze-v1.overlay.css": "cb937fae3166289c9c935d7ae25cefe3f82f3ec0",
    "css/glaze-v1.advanced.css": "d6e60a9b23354b1dc62dafac284c93b772e582a4",
    "css/glaze-v1.visual-refinement.css": "f5696fdb81f8deda3ce75e112989d772b7d74909",
    "css/glaze-v1.optical-reachability.css": "6123cff22f06b4c537156a1285e2664763f33316",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    require(manifest.get("schema") == "goreecloud.glaze-ui.web-source-manifest.v1", "unexpected web-source manifest schema")
    require(manifest.get("product") == "GLAZE UI V1.1", "unexpected product identity")
    require(manifest.get("version") == "1.1.0", "unexpected Stable machine version")
    require(manifest.get("tag") == "v1.1.0", "unexpected Stable tag")
    require(manifest.get("release_commit") == EXPECTED_RELEASE_COMMIT, "Stable release commit drifted")
    require(manifest.get("release_tree") == EXPECTED_RELEASE_TREE, "Stable release tree drifted")
    require(manifest.get("entrypoint") == EXPECTED_ENTRYPOINT, "Stable web entrypoint drifted")
    require(manifest.get("runtime_network_dependency_required") is False, "Stable web source must not require a runtime network dependency")
    require(manifest.get("files") == EXPECTED_FILES, "Stable web source file set/blob identities drifted")

    for relative, expected_sha in EXPECTED_FILES.items():
        path = ROOT / relative
        require(path.is_file(), f"missing Stable web source file: {relative}")
        actual_sha = git_blob_sha(path.read_bytes())
        require(actual_sha == expected_sha, f"Git blob identity drifted for {relative}: {actual_sha}")

    entrypoint = (ROOT / EXPECTED_ENTRYPOINT).read_text(encoding="utf-8")
    for required_import in (
        './glaze-v1.0.0.css',
        './glaze-v1.1.css',
        './glaze-v1.1-appearance.css',
    ):
        require(required_import in entrypoint, f"Stable entrypoint import missing: {required_import}")

    print("GLAZE UI V1.1 Stable web source manifest: OK")


if __name__ == "__main__":
    main()

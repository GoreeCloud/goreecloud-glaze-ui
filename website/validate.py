#!/usr/bin/env python3
from pathlib import Path
import hashlib
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "website"
DIST = SITE / "dist"
IDENTITY = ROOT / "assets" / "identity" / "official" / "facet"
# Approved canonical Glaze UI mark from GoreeCloud/goreecloud-branding-assets,
# commit 8aa413f7e5b50a0e9da65f3f8d173aa988d576bb, Git blob
# af8b70387bdaedb8d8388a1660b2d2ca29548fe2. The visual geometry is unchanged;
# this checksum reflects the corrected approved accessible title metadata.
CANONICAL_SHA256 = "82d3bdc331a96593873ca4d327e3b46d561d1ca96e653cef71e0c5e42fa1a31c"
LIVE_PRODUCT = "GLAZE UI V1.2"
LIVE_VERSION = "1.2.0"
TRANSITIONAL_ASSET_VERSION = "1.1.0"

for name in ("index.html", "404.html", "site.css", "identity.css", "site.js", "_headers", "build.py"):
    if not (SITE / name).is_file():
        raise SystemExit(f"missing website source: {name}")

for forbidden in (
    ROOT / "assets" / "identity" / "candidates" / "round-4",
    ROOT / "assets" / "identity" / "official" / "fold",
):
    if forbidden.exists():
        raise SystemExit(
            f"non-canonical identity path must not exist: {forbidden.relative_to(ROOT)}"
        )

mark = IDENTITY / "glaze-ui-mark.svg"
if not mark.is_file() or hashlib.sha256(mark.read_bytes()).hexdigest() != CANONICAL_SHA256:
    raise SystemExit("synchronized Facet source missing or changed")

# The repository website subtree is retained as transitional deployment/history
# material. Its build remains reproducible from the retained V1.1-era asset chain,
# while lifecycle/product copy must point to the live V1.2 Stable authority.
subprocess.run([sys.executable, str(SITE / "build.py")], cwd=ROOT, check=True)

required = (
    "index.html",
    "404.html",
    "_headers",
    "reference/v1-system-shell.html",
    "assets/site.css",
    "assets/identity.css",
    "assets/site.js",
    "assets/glaze-ui-mark.svg",
    "assets/glaze.css",
    "assets/glaze.controls.css",
    "assets/glaze.expressive.css",
    "assets/glaze.formfactors.css",
    "assets/glaze.accessibility.css",
    "assets/glaze.color.css",
    "assets/glaze.motion.css",
    "assets/glaze.materials.css",
    "assets/glaze.layout.css",
    "assets/glaze.states.css",
    "assets/glaze-v1.1.0.css",
    "assets/glaze-v1.1.css",
    "assets/glaze-v1.1-appearance.css",
    "assets/glaze-v1.0.0.css",
    "assets/glaze-v1.foundation.css",
    "assets/glaze-v1.components.css",
    "assets/glaze-v1.components.adaptive.css",
    "assets/glaze-v1.components.runtime.css",
    "assets/glaze-v1.structure.css",
    "assets/glaze-v1.overlay.css",
    "assets/glaze-v1.advanced.css",
    "assets/glaze-v1.visual-refinement.css",
    "assets/glaze-v1.optical-reachability.css",
)
for name in required:
    if not (DIST / name).is_file():
        raise SystemExit(f"missing build artifact: {name}")

if (DIST / "assets" / "glaze-ui-mark.svg").read_bytes() != mark.read_bytes():
    raise SystemExit("public identity asset drifted from Facet source")

# Former non-V1 product namespaces remain prohibited from the retained publication.
legacy_filename_markers = (
    "glaze-2.",
    "glaze-2-",
    "glaze-2_",
    "candidate",
    "2.2.0",
    "2.1.0",
    "2.0.0",
)
for path in DIST.rglob("*"):
    if path.is_file():
        rel = path.relative_to(DIST).as_posix().lower()
        if any(marker in rel for marker in legacy_filename_markers):
            raise SystemExit(f"former release namespace published in V1 artifact: {rel}")

html = (DIST / "index.html").read_text(encoding="utf-8")
not_found = (DIST / "404.html").read_text(encoding="utf-8")
headers = (DIST / "_headers").read_text(encoding="utf-8")
js = (DIST / "assets" / "site.js").read_text(encoding="utf-8")
entrypoint = (DIST / "assets" / "glaze-v1.1.0.css").read_text(encoding="utf-8")
base_entrypoint = (DIST / "assets" / "glaze-v1.0.0.css").read_text(encoding="utf-8")

for text in (
    LIVE_PRODUCT,
    f"<strong>{LIVE_VERSION}</strong>",
    "Current Stable authority",
    "transitional deployment/history material",
    "V1.1-era presentation assets",
    "GoreeCloud/goreecloud-static-websites",
    "Solid where you read. Glazed where you interact.",
    "Workspace → Application → System Overlay → System Panel → Critical System",
    "one dominant Glaze panel plus one to three small floating Glaze controls",
    "32 bounded contracts across five tiers.",
    "Universal Search",
    "Control Center",
    "exact source revision",
    "GoreeCloud/goreecloud-glaze-ui",
    "Skip to content",
):
    if text not in html:
        raise SystemExit(f"required transitional Design Center content missing: {text}")

# Fail closed if a former numbered Glaze product identity leaks into the current
# publication copy. V1.1 references are allowed only where the page explicitly
# describes the retained transitional asset chain or rollback history.
former_product_re = re.compile(r"\bglaze ui\s+v?(?:[2-9]\d*)(?:\.\d+){1,2}\b", re.IGNORECASE)
for surface_name, surface in (("index", html), ("404", not_found)):
    if former_product_re.search(surface):
        raise SystemExit(f"former Glaze product identity leaked into V1 {surface_name} surface")
    if ("glz" + "22") in surface.lower():
        raise SystemExit(f"former internal release namespace leaked into V1 {surface_name} surface")
    if ("glaze-" + "2" + ".") in surface.lower():
        raise SystemExit(f"former stylesheet release namespace leaked into V1 {surface_name} surface")
    if "/assets/glaze-v1.0.css" in surface:
        raise SystemExit(f"pre-reset V1-alias asset leaked into current {surface_name} surface")

for text in (
    LIVE_PRODUCT,
    LIVE_VERSION,
    "Current Stable authority",
    "transitional deployment/history material",
    "GoreeCloud/goreecloud-static-websites",
    "/assets/glaze-v1.1.0.css",
):
    if text not in not_found:
        raise SystemExit(f"transitional V1 404 surface missing: {text}")

# The retained site intentionally publishes its prior Stable presentation chain;
# that is allowed only because the visible site copy declares the boundary above.
for marker in (
    '@import url("./glaze-v1.0.0.css")',
    '@import url("./glaze-v1.1.css")',
    '@import url("./glaze-v1.1-appearance.css")',
):
    if marker not in entrypoint:
        raise SystemExit(f"transitional V1.1 asset entrypoint missing required source layer: {marker}")

for marker in (
    '@import url("./glaze-v1.foundation.css")',
    '@import url("./glaze-v1.components.css")',
    '@import url("./glaze-v1.components.adaptive.css")',
    '@import url("./glaze-v1.components.runtime.css")',
    '@import url("./glaze-v1.structure.css")',
    '@import url("./glaze-v1.overlay.css")',
    '@import url("./glaze-v1.advanced.css")',
    '@import url("./glaze-v1.visual-refinement.css")',
    '@import url("./glaze-v1.optical-reachability.css")',
):
    if marker not in base_entrypoint:
        raise SystemExit(f"inherited V1 structural entrypoint missing required layer: {marker}")

# Every local published asset referenced by the two HTML entry surfaces must exist.
for surface_name, surface in (("index", html), ("404", not_found)):
    for asset in re.findall(r'(?:src|href)=["\'](/assets/[^"\']+)', surface):
        if not (DIST / asset.removeprefix("/")).is_file():
            raise SystemExit(f"{surface_name} references missing public asset: {asset}")

if "/reference/v1-system-shell.html" not in html:
    raise SystemExit("V1 System Shell public reference link missing")

for remote in re.findall(r'(?:src|href)=["\'](https?://[^"\']+)', html + not_found):
    if "github.com/GoreeCloud/goreecloud-glaze-ui" not in remote:
        raise SystemExit(f"unexpected remote browser resource/link: {remote}")

for directive in (
    "Content-Security-Policy:",
    "frame-ancestors 'none'",
    "Permissions-Policy:",
    "X-Content-Type-Options: nosniff",
):
    if directive not in headers:
        raise SystemExit(f"required security header missing: {directive}")

if "localStorage" not in js or "data-theme-choice" not in html:
    raise SystemExit("local appearance preference contract missing")

print(
    f"GLAZE UI Design Center transitional validation passed: live authority {LIVE_PRODUCT} / {LIVE_VERSION}; "
    f"retained V{TRANSITIONAL_ASSET_VERSION} presentation asset chain is explicitly disclosed as transitional, "
    "Facet identity is synchronized, and required security headers are present."
)

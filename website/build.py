#!/usr/bin/env python3
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "website"
DIST = SOURCE / "dist"
IDENTITY = ROOT / "assets" / "identity" / "official" / "facet"
REFERENCE = ROOT / "reference"

if DIST.exists():
    shutil.rmtree(DIST)
(DIST / "assets").mkdir(parents=True)
(DIST / "reference").mkdir(parents=True)

for name in ("index.html", "404.html", "_headers"):
    shutil.copy2(SOURCE / name, DIST / name)

for name in ("site.css", "identity.css", "site.js"):
    shutil.copy2(SOURCE / name, DIST / "assets" / name)

# This retained repository website subtree is a transitional publication/history
# surface. It publishes the generic foundations and preserved V1.1 presentation
# chain required by that snapshot; live lifecycle authority is GLAZE UI V1.3 / 1.3.0.
# Canonical public static-site source lives in GoreeCloud/goreecloud-static-websites.
for name in (
    "glaze.css",
    "glaze.controls.css",
    "glaze.expressive.css",
    "glaze.formfactors.css",
    "glaze.accessibility.css",
    "glaze.color.css",
    "glaze.motion.css",
    "glaze.materials.css",
    "glaze.layout.css",
    "glaze.states.css",
    "glaze-v1.1.0.css",
    "glaze-v1.1.css",
    "glaze-v1.1-appearance.css",
    "glaze-v1.0.0.css",
    "glaze-v1.foundation.css",
    "glaze-v1.components.css",
    "glaze-v1.components.adaptive.css",
    "glaze-v1.components.runtime.css",
    "glaze-v1.structure.css",
    "glaze-v1.overlay.css",
    "glaze-v1.advanced.css",
    "glaze-v1.visual-refinement.css",
    "glaze-v1.optical-reachability.css",
):
    shutil.copy2(ROOT / "css" / name, DIST / "assets" / name)

shutil.copy2(IDENTITY / "glaze-ui-mark.svg", DIST / "assets" / "glaze-ui-mark.svg")
shutil.copy2(REFERENCE / "v1-system-shell.html", DIST / "reference" / "v1-system-shell.html")

print(
    f"Built {DIST.relative_to(ROOT)} as a transitional Design Center snapshot under "
    "GLAZE UI V1.3 / 1.3.0 current Stable authority, using the explicitly retained "
    "V1.1 presentation asset chain"
)

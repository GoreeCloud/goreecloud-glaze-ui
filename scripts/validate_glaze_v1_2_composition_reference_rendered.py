#!/usr/bin/env python3
"""Rendered acceptance for the bounded GLAZE UI V1.2 canonical composition reference library."""
from __future__ import annotations

import base64
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
HOST = "127.0.0.1"
WEB_PORT = 8798
DRIVER_PORT = 9548
SERVER = f"http://{HOST}:{WEB_PORT}"
DRIVER = f"http://{HOST}:{DRIVER_PORT}"
REFERENCE = "reference/v1.2/composition-reference-library.html"
CONTRACT = ROOT / "contracts/v1.2/composition-reference-library.candidate.json"
CSS = ROOT / "css/glaze-v1.2-composition-reference.candidate.css"
ENTRYPOINT = ROOT / "css/glaze-v1.2.0-candidate.css"
WORKFLOW = ROOT / ".github/workflows/glaze-v1.2-composition-reference.yml"
SPATIAL = ROOT / "contracts/v1.2/spatial-foundation.candidate.json"
FORM_FACTOR = ROOT / "contracts/v1.2/form-factor-tokens.candidate.json"
EXPECTED = [
    "home-dashboard",
    "data-heavy-administration",
    "settings",
    "file-browser",
    "search",
    "form",
    "detail-inspector",
    "media",
]


class AcceptanceError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AcceptanceError(message)


def load(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected object in {path.relative_to(ROOT)}")
    return value


def validate_source() -> None:
    for path in (CONTRACT, CSS, ENTRYPOINT, WORKFLOW, ROOT / REFERENCE, SPATIAL, FORM_FACTOR):
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    contract = load(CONTRACT)
    spatial = load(SPATIAL)
    form_factor = load(FORM_FACTOR)
    require(contract.get("version") == "1.2.0-candidate", "composition contract version drifted")
    require(contract.get("lifecycle") == "candidate" and contract.get("consumerEligible") is False, "composition Candidate boundary drifted")
    require(contract.get("stableBaseline") == "1.1.0", "composition Stable baseline drifted")
    require(contract.get("status") == "bounded-composition-reference-library", "composition contract status drifted")
    require(contract.get("referenceCompositions") == EXPECTED, "canonical reference composition set/order drifted")
    authority = contract.get("authority", {})
    require(authority.get("spatialFoundation") == "contracts/v1.2/spatial-foundation.candidate.json", "spatial authority binding drifted")
    require(authority.get("formFactorTokens") == "contracts/v1.2/form-factor-tokens.candidate.json", "form-factor authority binding drifted")
    rules = contract.get("compositionRules", {})
    for key in (
        "primaryTaskVisuallyDominant",
        "primarySecondaryTertiaryRegionsDistinct",
        "stableNavigationSpatialMemory",
        "durableReadingSurfacesBackdropDependent",
        "floatingInteractionMayUseExistingGlaze",
        "cardOverloadProhibited",
        "spacePreferredBeforeHeavyDividers",
        "responsiveTransformationRequired",
        "desktopSqueezedIntoCompactProhibited",
        "inspectorTransformsWhenSpaceInsufficient",
        "semanticOrderPreservedAcrossComposition",
        "noNewNumericSpatialCalibration",
        "noNewMaterialCalibration",
    ):
        expected = False if key == "durableReadingSurfacesBackdropDependent" else True
        require(rules.get(key) is expected, f"composition rule drifted: {key}")
    acceptance = contract.get("acceptance", {})
    require(acceptance.get("layoutClasses") == ["expanded", "compact"], "composition layout acceptance drifted")
    require(acceptance.get("compactViewportWidthPx") == 390, "compact acceptance width drifted")
    require(acceptance.get("textScalePercent") == 200, "text scale acceptance drifted")
    require(acceptance.get("minimumInteractiveTargetPx") == 48, "target floor drifted")
    require(acceptance.get("horizontalPageOverflowProhibited") is True, "page overflow prohibition drifted")
    require(spatial.get("surfaceRelationship", {}).get("durableReadingZonesBackdropDependent") is False, "spatial durable-surface authority drifted")
    require(spatial.get("capabilityClassRule", {}).get("platformAdapterSelectsCapabilityClass") is True, "spatial capability authority drifted")
    require(form_factor.get("rules", {}).get("consumerClaimBlocked") is True, "form-factor Candidate boundary drifted")

    css = CSS.read_text(encoding="utf-8")
    require("blur(" not in css.lower(), "composition layer introduced blur")
    require("@media (max-width" not in css.lower() and "@media (min-width" not in css.lower(), "composition layer introduced viewport-as-device breakpoint authority")
    for marker in (
        ".glz12-composition-library",
        ".glz12-composition-scene",
        ".glz12-composition-primary",
        ".glz12-composition-inspector",
        '[data-glz-layout-class="compact"]',
        '[data-transform="bottom"]',
        '[data-glz-transparency="reduced"]',
        "@media (forced-colors: active)",
    ):
        require(marker in css, f"composition CSS marker missing: {marker}")

    reference = (ROOT / REFERENCE).read_text(encoding="utf-8")
    for name in EXPECTED:
        require(f'data-composition="{name}"' in reference, f"reference composition missing: {name}")
    for marker in (
        'id="home-nav"',
        'id="files-nav"',
        'id="detail-inspector"',
        'role="search"',
        'role="toolbar"',
        'role="listbox"',
        'role="status"',
        'data-glaze-density-profile="productive"',
        'data-glaze-density-profile="immersive"',
    ):
        require(marker in reference, f"composition reference semantic marker missing: {marker}")

    entry = ENTRYPOINT.read_text(encoding="utf-8")
    chain = [
        '@import url("./glaze-v1.2-spatial-foundation.candidate.css")',
        '@import url("./glaze-v1.2-composition-reference.candidate.css")',
        '@import url("./glaze-v1.2-geometry.candidate.css")',
        '@import url("./glaze-v1.2-accessibility.candidate.css")',
    ]
    require(all(item in entry for item in chain), "Candidate entrypoint missing composition import chain")
    require([entry.index(item) for item in chain] == sorted(entry.index(item) for item in chain), "composition import order drifted")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    require("validate_glaze_v1_2_composition_reference_rendered.py" in workflow, "composition workflow does not invoke rendered validator")
    require("github.event.pull_request.head.sha || github.sha" in workflow, "composition workflow is not exact-head pinned")


def request(method: str, path: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> Any:
    req = Request(
        f"{DRIVER}{path}",
        data=None if payload is None else json.dumps(payload).encode(),
        method=method,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as error:
        raise AcceptanceError(f"WebDriver HTTP {error.code}: {error.read().decode(errors='replace')}") from error
    except (URLError, TimeoutError) as error:
        raise AcceptanceError(f"WebDriver request failed: {error}") from error
    if not raw:
        return None
    value = json.loads(raw.decode()).get("value")
    if isinstance(value, dict) and value.get("error"):
        raise AcceptanceError(f"WebDriver {value.get('error')}: {value.get('message', '')}")
    return value


def wait_http(url: str, seconds: float = 15) -> None:
    end = time.monotonic() + seconds
    last: Exception | None = None
    while time.monotonic() < end:
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except Exception as error:
            last = error
        time.sleep(.15)
    raise AcceptanceError(f"HTTP endpoint not ready: {last}")


def chromedriver() -> str:
    for item in (shutil.which("chromedriver"), "/usr/bin/chromedriver", "/usr/local/share/chromedriver-linux64/chromedriver"):
        if item and Path(item).is_file():
            return str(item)
    raise AcceptanceError("chromedriver unavailable")


def wait_driver() -> None:
    end = time.monotonic() + 15
    last: Exception | None = None
    while time.monotonic() < end:
        try:
            status = request("GET", "/status")
            if isinstance(status, dict) and status.get("ready"):
                return
        except Exception as error:
            last = error
        time.sleep(.2)
    raise AcceptanceError(f"chromedriver not ready: {last}")


def session() -> str:
    value = request("POST", "/session", {"capabilities": {"alwaysMatch": {
        "browserName": "chrome",
        "goog:chromeOptions": {"args": [
            "--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-background-networking",
            "--disable-component-update", "--disable-extensions", "--disable-sync", "--metrics-recording-only",
            "--no-first-run", "--window-size=1280,1200",
        ]},
    }}}, timeout=60)
    require(isinstance(value, dict) and isinstance(value.get("sessionId"), str), "Chrome returned no session id")
    return value["sessionId"]


def execute(sid: str, script: str) -> Any:
    return request("POST", f"/session/{sid}/execute/sync", {"script": script, "args": []})


def cdp(sid: str, cmd: str, params: dict[str, Any] | None = None) -> Any:
    return request("POST", f"/session/{sid}/goog/cdp/execute", {"cmd": cmd, "params": params or {}})


def viewport(sid: str, width: int, height: int) -> None:
    cdp(sid, "Emulation.setDeviceMetricsOverride", {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": False, "screenWidth": width, "screenHeight": height})


def media(sid: str, features: list[dict[str, str]]) -> None:
    cdp(sid, "Emulation.setEmulatedMedia", {"media": "screen", "features": features})


def navigate(sid: str) -> None:
    request("POST", f"/session/{sid}/url", {"url": f"{SERVER}/{REFERENCE}"})
    end = time.monotonic() + 15
    while time.monotonic() < end:
        if execute(sid, "return document.readyState") == "complete":
            return
        time.sleep(.1)
    raise AcceptanceError("composition reference did not finish loading")


def screenshot(sid: str, name: str) -> None:
    encoded = request("GET", f"/session/{sid}/screenshot")
    require(isinstance(encoded, str) and encoded, "no screenshot bytes")
    ARTIFACTS.mkdir(exist_ok=True)
    path = ARTIFACTS / f"glaze-v1.2-composition-reference-{name}.png"
    path.write_bytes(base64.b64decode(encoded))
    require(path.stat().st_size > 7000, f"invalid screenshot {path}")


STATE_JS = r"""
const names=[...document.querySelectorAll('[data-composition]')].map(e=>e.dataset.composition);
const scenes=[...document.querySelectorAll('[data-composition]')].map(scene=>{
  const durable=[...scene.querySelectorAll('.glz12-composition-primary,.glz12-composition-reading,.glz12-composition-data-plane')].map(el=>{const s=getComputedStyle(el);return s.backdropFilter||s.webkitBackdropFilter||'none';});
  const actions=[...scene.querySelectorAll('.glz12-composition-action')].map(el=>{const r=el.getBoundingClientRect();return {w:r.width,h:r.height};});
  return {name:scene.dataset.composition,layout:scene.dataset.glzLayoutClass,durable,actions};
});
const homeNav=[...document.querySelectorAll('#home-nav > *')].map(e=>e.textContent.trim());
const filesNav=[...document.querySelectorAll('#files-nav > *')].map(e=>e.textContent.trim());
const detailScene=document.querySelector('#scene-inspector');
const detailPrimary=detailScene.querySelector('.glz12-composition-primary').getBoundingClientRect();
const detailInspector=document.querySelector('#detail-inspector').getBoundingClientRect();
const homeScene=document.querySelector('#scene-home');
const homeGrid=homeScene.querySelector('.glz12-layout-grid').getBoundingClientRect();
const homeNavRect=document.querySelector('#home-nav').getBoundingClientRect();
return {
  ready:document.readyState,
  width:innerWidth,
  scrollWidth:document.documentElement.scrollWidth,
  names,
  scenes,
  homeNav,
  filesNav,
  detail:{primaryBottom:detailPrimary.bottom,inspectorTop:detailInspector.top},
  home:{gridBottom:homeGrid.bottom,navTop:homeNavRect.top},
  textScale:document.documentElement.dataset.glzTextScale||'',
  transparency:document.documentElement.dataset.glzTransparency||'',
  dir:document.documentElement.dir||'ltr'
};
"""


def state(sid: str) -> dict[str, Any]:
    value = execute(sid, STATE_JS)
    require(isinstance(value, dict), f"could not read composition state: {value!r}")
    return value


def identity(value: dict[str, Any], width: int) -> None:
    require(value.get("ready") == "complete", f"composition page not complete: {value}")
    require(abs(int(value.get("width", 0)) - width) <= 1, f"composition viewport mismatch: {value}")
    require(int(value.get("scrollWidth", width + 2)) <= width + 1, f"composition page has horizontal overflow: {value}")
    require(value.get("names") == EXPECTED, f"rendered composition set/order drifted: {value.get('names')}")
    for scene in value.get("scenes", []):
        require(all(item == "none" for item in scene.get("durable", [])), f"durable composition became backdrop-dependent: {scene}")
        require(all(float(item.get("w", 0)) >= 48 and float(item.get("h", 0)) >= 48 for item in scene.get("actions", [])), f"48 px action target floor drifted: {scene}")
    require(value.get("homeNav") == ["Home", "Activity", "Files"], f"Home navigation spatial order drifted: {value.get('homeNav')}")
    require(value.get("filesNav") == ["Files", "Shared", "Recent"], f"Files navigation spatial order drifted: {value.get('filesNav')}")


def main() -> int:
    http = driver = None
    sid: str | None = None
    try:
        validate_source()
        ARTIFACTS.mkdir(exist_ok=True)
        http = subprocess.Popen([sys.executable, "-m", "http.server", str(WEB_PORT), "--bind", HOST, "--directory", str(ROOT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wait_http(f"{SERVER}/{REFERENCE}")
        driver = subprocess.Popen([chromedriver(), f"--port={DRIVER_PORT}", "--allowed-ips=127.0.0.1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wait_driver()
        sid = session()
        media(sid, [])
        viewport(sid, 1280, 1200)
        navigate(sid)
        expanded = state(sid)
        identity(expanded, 1280)
        require(all(scene.get("layout") == "expanded" for scene in expanded.get("scenes", [])), f"expanded composition class drifted: {expanded}")
        screenshot(sid, "expanded")

        viewport(sid, 390, 1200)
        execute(sid, "document.documentElement.dataset.glzTextScale='200';document.querySelectorAll('[data-composition]').forEach(e=>e.dataset.glzLayoutClass='compact');return true;")
        compact = state(sid)
        identity(compact, 390)
        require(all(scene.get("layout") == "compact" for scene in compact.get("scenes", [])), f"compact composition class drifted: {compact}")
        require(compact.get("textScale") == "200", f"200% text acceptance state missing: {compact}")
        require(float(compact["detail"]["inspectorTop"]) >= float(compact["detail"]["primaryBottom"]) - 1, f"compact inspector did not transform below primary task: {compact}")
        require(float(compact["home"]["navTop"]) >= float(compact["home"]["gridBottom"]) - 1, f"compact navigation did not transform after primary content: {compact}")
        screenshot(sid, "compact-200")

        execute(sid, "document.documentElement.dataset.glzTransparency='reduced';document.documentElement.dir='rtl';return true;")
        reduced = state(sid)
        identity(reduced, 390)
        require(reduced.get("transparency") == "reduced" and reduced.get("dir") == "rtl", f"reduced-transparency/RTL state missing: {reduced}")

        media(sid, [{"name": "forced-colors", "value": "active"}])
        forced = state(sid)
        identity(forced, 390)
        screenshot(sid, "forced-colors-rtl")

        print("GLAZE UI V1.2 composition reference library validated: 8 canonical scenes; expanded/compact/200%/RTL/forced-colors gates PASS")
        return 0
    finally:
        if sid:
            try:
                request("DELETE", f"/session/{sid}")
            except Exception:
                pass
        for process in (driver, http):
            if process is not None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except Exception:
                    process.kill()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AcceptanceError as error:
        print(f"GLAZE UI V1.2 composition reference acceptance failed: {error}")
        raise SystemExit(1)

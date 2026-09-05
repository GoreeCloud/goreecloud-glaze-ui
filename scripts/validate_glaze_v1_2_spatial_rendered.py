#!/usr/bin/env python3
"""Bounded rendered-web acceptance for the GLAZE UI V1.2 spatial foundation Candidate."""
from __future__ import annotations

import base64, json, shutil, subprocess, sys, time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
HOST = "127.0.0.1"
WEB_PORT = 8789
DRIVER_PORT = 9539
SERVER = f"http://{HOST}:{WEB_PORT}"
DRIVER = f"http://{HOST}:{DRIVER_PORT}"
REFERENCE = "reference/v1.2/spatial-foundation.html"
CONTRACT = ROOT / "contracts/v1.2/spatial-foundation.candidate.json"
TOKENS = ROOT / "tokens/glaze-v1.2-spatial-foundation.candidate.json"
CSS = ROOT / "css/glaze-v1.2-spatial-foundation.candidate.css"
ENTRYPOINT = ROOT / "css/glaze-v1.2.0-candidate.css"
SPACING = [2, 4, 8, 12, 16, 24, 32, 48, 64, 96]
CAPABILITIES = {
    "compact": (390, 16, 4, True),
    "medium": (820, 24, 8, False),
    "expanded": (1280, 32, 12, False),
    "large": (1600, 48, 12, False),
}
DENSITIES = {
    "comfortable": (24, 48),
    "standard": (16, 32),
    "productive": (12, 24),
    "immersive": (24, 48),
}

class AcceptanceError(RuntimeError):
    pass

def require(ok: bool, message: str) -> None:
    if not ok:
        raise AcceptanceError(message)

def validate_source() -> None:
    for path in (CONTRACT, TOKENS, CSS, ENTRYPOINT, ROOT / REFERENCE):
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    c = json.loads(CONTRACT.read_text(encoding="utf-8"))
    t = json.loads(TOKENS.read_text(encoding="utf-8"))
    require(c.get("version") == "1.2.0-candidate", "spatial contract version drifted")
    require(c.get("lifecycle") == "candidate" and c.get("consumerEligible") is False, "spatial Candidate lifecycle boundary drifted")
    require(c.get("stableBaseline") == "1.1.0", "spatial Stable baseline drifted")
    require(c.get("spacingScalePx") == SPACING, "canonical spatial spacing scale drifted")
    require(list(c.get("spacingRoles", {}).values()) == SPACING, "semantic spacing role map drifted")
    classes = c.get("layoutCapabilityClasses", {})
    require({k: (v.get("gutterPx"), v.get("gridColumns")) for k, v in classes.items()} == {
        "compact": (16, 4), "medium": (24, 8), "expanded": (32, 12), "large": (48, 12)
    }, "layout capability contract drifted")
    rule = c.get("capabilityClassRule", {})
    require(rule.get("deviceBrandBreakpointsAreCanonical") is False and rule.get("platformAdapterSelectsCapabilityClass") is True, "capability-class authority boundary drifted")
    require(c.get("quietZones", {}).get("defaultBlockSpacePx") == 48, "Quiet Zone default drifted")
    require(c.get("densityRules", {}).get("densityIsNotScale") is True, "density-is-not-scale rule drifted")
    require(c.get("densityRules", {}).get("minimumInteractiveTargetPx") == 48, "interactive target floor drifted")
    require(c.get("surfaceRelationship", {}).get("spatialLayerIntroducesNewBackdropBlur") is False, "spatial blur boundary drifted")
    impl = c.get("implementation", {})
    require(impl.get("tokens") == "tokens/glaze-v1.2-spatial-foundation.candidate.json", "spatial token binding drifted")
    require(impl.get("webLayer") == "css/glaze-v1.2-spatial-foundation.candidate.css", "spatial CSS binding drifted")
    require(impl.get("reference") == REFERENCE, "spatial reference binding drifted")
    require(impl.get("renderedValidator") == "scripts/validate_glaze_v1_2_spatial_rendered.py", "spatial validator binding drifted")
    require(t.get("version") == "1.2.0-candidate" and t.get("consumerEligible") is False, "spatial token lifecycle drifted")
    require(list(t.get("spacePx", {}).values()) == SPACING, "spatial token scale drifted")
    require(t.get("guttersPx") == {"compact": 16, "medium": 24, "expanded": 32, "large": 48}, "gutter tokens drifted")
    require(t.get("gridColumns") == {"compact": 4, "medium": 8, "expanded": 12, "large": 12}, "grid tokens drifted")
    require(t.get("targets", {}).get("minimumInteractivePx") == 48, "target token drifted")
    text = CSS.read_text(encoding="utf-8") + "\n" + (ROOT / REFERENCE).read_text(encoding="utf-8")
    for marker in (
        "--glz12-space-micro: 2px", "--glz12-space-page-hero: 96px", 'data-glz-layout-class="compact"',
        "--glz12-grid-columns: 12", ".glz12-quiet-zone", ".glz12-durable-reading-zone",
        'data-glaze-density-profile="productive"', "@media (forced-colors: active)"
    ):
        require(marker in text, f"spatial implementation marker missing: {marker}")
    require("blur(" not in CSS.read_text(encoding="utf-8").lower(), "spatial layer must not introduce blur")
    entry = ENTRYPOINT.read_text(encoding="utf-8")
    chain = [
        '@import url("./glaze-v1.2-crystal-icons.candidate.css")',
        '@import url("./glaze-v1.2-typography.candidate.css")',
        '@import url("./glaze-v1.2-spatial-foundation.candidate.css")',
        '@import url("./glaze-v1.2-accessibility.candidate.css")',
    ]
    require(all(x in entry for x in chain), "Candidate entrypoint missing spatial import chain")
    require([entry.index(x) for x in chain] == sorted(entry.index(x) for x in chain), "spatial/accessibility import order drifted")

def request(method: str, path: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> Any:
    req = Request(f"{DRIVER}{path}", data=None if payload is None else json.dumps(payload).encode(), method=method, headers={"Content-Type": "application/json; charset=utf-8"})
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
            s = request("GET", "/status")
            if isinstance(s, dict) and s.get("ready"):
                return
        except Exception as error:
            last = error
        time.sleep(.2)
    raise AcceptanceError(f"chromedriver not ready: {last}")

def session() -> str:
    value = request("POST", "/session", {"capabilities": {"alwaysMatch": {"browserName": "chrome", "goog:chromeOptions": {"args": [
        "--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-background-networking",
        "--disable-component-update", "--disable-extensions", "--disable-sync", "--metrics-recording-only",
        "--no-first-run", "--window-size=1280,960"
    ]}}}}, timeout=60)
    require(isinstance(value, dict) and isinstance(value.get("sessionId"), str), "Chrome returned no session id")
    return value["sessionId"]

def execute(sid: str, script: str) -> Any:
    return request("POST", f"/session/{sid}/execute/sync", {"script": script, "args": []})

def cdp(sid: str, cmd: str, params: dict[str, Any] | None = None) -> Any:
    return request("POST", f"/session/{sid}/goog/cdp/execute", {"cmd": cmd, "params": params or {}})

def viewport(sid: str, width: int, height: int) -> None:
    # Capability-class acceptance uses an exact CSS viewport, not device/UA emulation.
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
    raise AcceptanceError("spatial reference did not finish loading")

def screenshot(sid: str, name: str) -> None:
    encoded = request("GET", f"/session/{sid}/screenshot")
    require(isinstance(encoded, str) and encoded, "no screenshot bytes")
    ARTIFACTS.mkdir(exist_ok=True)
    path = ARTIFACTS / f"glaze-v1.2-spatial-{name}.png"
    path.write_bytes(base64.b64decode(encoded))
    require(path.stat().st_size > 7000, f"invalid screenshot {path}")

STATE_JS = r"""
const root=document.documentElement, frame=document.querySelector('#layout-frame'), grid=document.querySelector('#composition-grid');
const fc=getComputedStyle(frame), gc=getComputedStyle(grid), stack=getComputedStyle(frame.querySelector(':scope > .glz12-spatial-stack')), cluster=getComputedStyle(document.querySelector('#density-cluster'));
const quiet=getComputedStyle(document.querySelector('#quiet-zone')), ordinary=getComputedStyle(document.querySelector('#ordinary-section'));
const durable=getComputedStyle(document.querySelector('#durable-zone')), floating=getComputedStyle(document.querySelector('#floating-zone .glz1-toolbar'));
const bodyType=getComputedStyle(document.querySelector('[data-glz-type="body"]'));
const primary=document.querySelector('#durable-zone').getBoundingClientRect(), secondary=document.querySelector('#floating-zone').getBoundingClientRect();
const cols=gc.gridTemplateColumns.split(/\s+/).filter(Boolean).length;
const targets=[...document.querySelectorAll('.glz12-spatial-action')].map(e=>{const r=e.getBoundingClientRect();return {w:r.width,h:r.height};});
return {ready:document.readyState,width:innerWidth,scrollWidth:document.documentElement.scrollWidth,version:root.dataset.glazeVersion,upgrade:root.dataset.glazeUpgrade,density:root.dataset.glazeDensityProfile,layoutClass:frame.dataset.glzLayoutClass,gutter:parseFloat(fc.paddingLeft),logicalColumns:parseFloat(fc.getPropertyValue('--glz12-grid-columns')),renderedColumns:cols,gridGap:parseFloat(gc.columnGap),stackGap:parseFloat(stack.rowGap),clusterGap:parseFloat(cluster.columnGap),quietTop:parseFloat(quiet.paddingTop),ordinaryTop:parseFloat(ordinary.paddingTop),bodySize:parseFloat(bodyType.fontSize),durableFilter:durable.backdropFilter||durable.webkitBackdropFilter||'none',floatingFilter:floating.backdropFilter||floating.webkitBackdropFilter||'none',primary:{top:primary.top,bottom:primary.bottom},secondary:{top:secondary.top,bottom:secondary.bottom},targets};
"""

def state(sid: str) -> dict[str, Any]:
    value = execute(sid, STATE_JS)
    require(isinstance(value, dict), f"could not read spatial state: {value!r}")
    return value

def identity(s: dict[str, Any], width: int) -> None:
    require(s.get("ready") == "complete" and abs(int(s.get("width", 0)) - width) <= 1, f"page/viewport mismatch: {s}")
    require(int(s.get("scrollWidth", width + 2)) <= width + 1, f"horizontal overflow: {s}")
    require(s.get("version") == "1.1" and s.get("upgrade") == "v1.2-frosted-neutral", "Candidate activation boundary missing")
    require(s.get("durableFilter") == "none", f"durable reading surface became backdrop-dependent: {s}")
    require(all(float(x.get("w", 0)) >= 48 and float(x.get("h", 0)) >= 48 for x in s.get("targets", [])), f"48 px target floor drifted: {s.get('targets')}")

def set_layout(sid: str, name: str, width: int) -> dict[str, Any]:
    viewport(sid, width, 960)
    execute(sid, f"document.querySelector('#layout-frame').setAttribute('data-glz-layout-class','{name}');return true;")
    return state(sid)

def validate_capability(s: dict[str, Any], name: str, gutter: int, columns: int, stacked: bool) -> None:
    require(s.get("layoutClass") == name, f"layout capability class inactive: {s}")
    require(abs(float(s.get("gutter", -1)) - gutter) < .2, f"{name} gutter drifted: {s}")
    require(round(float(s.get("logicalColumns", -1))) == columns and int(s.get("renderedColumns", -1)) == columns, f"{name} grid columns drifted: {s}")
    if stacked:
        require(float(s["secondary"]["top"]) >= float(s["primary"]["bottom"]) - 1, f"compact composition did not stack regions: {s}")
    else:
        require(abs(float(s["secondary"]["top"]) - float(s["primary"]["top"])) < 2, f"{name} composition did not share primary row: {s}")

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
        viewport(sid, 1280, 960)
        navigate(sid)

        execute(sid, "document.documentElement.setAttribute('data-glaze-density-profile','standard');return true;")
        for name, (width, gutter, columns, stacked) in CAPABILITIES.items():
            s = set_layout(sid, name, width)
            identity(s, width)
            validate_capability(s, name, gutter, columns, stacked)
            require(float(s["quietTop"]) > float(s["ordinaryTop"]), f"Quiet Zone lost hierarchy: {s}")
            if name in ("compact", "expanded"):
                screenshot(sid, f"{name}-standard")

        viewport(sid, 1280, 960)
        execute(sid, "document.querySelector('#layout-frame').setAttribute('data-glz-layout-class','expanded');return true;")
        body_size = None
        for name, (cluster_gap, section_gap) in DENSITIES.items():
            execute(sid, f"document.documentElement.setAttribute('data-glaze-density-profile','{name}');return true;")
            s = state(sid)
            identity(s, 1280)
            require(abs(float(s["clusterGap"]) - cluster_gap) < .2, f"{name} cluster spacing drifted: {s}")
            require(abs(float(s["stackGap"]) - section_gap) < .2, f"{name} section spacing drifted: {s}")
            body_size = float(s["bodySize"]) if body_size is None else body_size
            require(abs(float(s["bodySize"]) - body_size) < .2, f"density improperly scaled typography: {s}")
            if name == "productive":
                screenshot(sid, "expanded-productive")

        execute(sid, "document.documentElement.setAttribute('data-glaze-density-profile','standard');return true;")
        normal = state(sid)
        require(normal.get("floatingFilter") not in (None, "", "none"), f"existing floating Glaze material was not preserved: {normal}")
        media(sid, [{"name": "forced-colors", "value": "active"}])
        forced = state(sid)
        identity(forced, 1280)
        require(abs(float(forced["gutter"]) - 32) < .2 and int(forced["renderedColumns"]) == 12, f"Forced Colors changed spatial hierarchy: {forced}")
        require(forced.get("floatingFilter") == "none", f"Forced Colors did not remove floating optical blur: {forced}")
        screenshot(sid, "forced-colors")

        media(sid, [])
        viewport(sid, 390, 844)
        execute(sid, "document.querySelector('#layout-frame').setAttribute('data-glz-layout-class','compact');document.documentElement.style.fontSize='200%';return true;")
        large = state(sid)
        identity(large, 390)
        validate_capability(large, "compact", 16, 4, True)
        require(float(large.get("bodySize", 0)) >= 31.5, f"200% text scaling did not apply: {large}")
        screenshot(sid, "compact-200-percent")

        print("GLAZE UI V1.2 spatial foundation rendered validation passed.")
        print("Boundary: bounded web spatial Candidate evidence only; V1.1 remains Stable and V1.2 remains non-consumer-eligible.")
        return 0
    except Exception as error:
        print(f"GLAZE UI V1.2 spatial foundation rendered validation failed: {error}", file=sys.stderr)
        return 1
    finally:
        if sid:
            try:
                request("DELETE", f"/session/{sid}")
            except Exception:
                pass
        for process in (driver, http):
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()

if __name__ == "__main__":
    raise SystemExit(main())

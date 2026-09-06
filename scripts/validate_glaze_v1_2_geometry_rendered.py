#!/usr/bin/env python3
"""Bounded rendered-web acceptance for the GLAZE UI V1.2 geometry Candidate."""
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
WEB_PORT = 8790
DRIVER_PORT = 9540
SERVER = f"http://{HOST}:{WEB_PORT}"
DRIVER = f"http://{HOST}:{DRIVER_PORT}"
REFERENCE = "reference/v1.2/geometry.html"
CONTRACT = ROOT / "contracts/v1.2/geometry.candidate.json"
TOKENS = ROOT / "tokens/glaze-v1.2-geometry.candidate.json"
CSS = ROOT / "css/glaze-v1.2-geometry.candidate.css"
ENTRYPOINT = ROOT / "css/glaze-v1.2.0-candidate.css"
WORKFLOW = ROOT / ".github/workflows/glaze-v1.2-geometry.yml"

EXPECTED = {
    "checkbox": 7,
    "tooltip": 10,
    "button-xs": 10,
    "button": 12,
    "button-xl": 16,
    "field": 14,
    "toolbar": 16,
    "menu": 16,
    "menu-item": 10,
    "card": 20,
    "card-button": 12,
    "popover": 20,
    "popover-field": 14,
    "dialog": 24,
    "smart-rail": 26,
    "dock": 28,
    "dock-item": 16,
    "sheet": 28,
    "sheet-button": 12,
    "capsule": 999,
    "capsule-expanded": 24,
    "morph": 24,
    "morph-expanded": 28,
}

class AcceptanceError(RuntimeError):
    pass

def require(ok: bool, message: str) -> None:
    if not ok:
        raise AcceptanceError(message)

def validate_source() -> None:
    for path in (CONTRACT, TOKENS, CSS, ENTRYPOINT, WORKFLOW, ROOT / REFERENCE):
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    tokens = json.loads(TOKENS.read_text(encoding="utf-8"))
    require(contract.get("version") == "1.2.0-candidate", "geometry contract version drifted")
    require(contract.get("lifecycle") == "candidate" and contract.get("consumerEligible") is False, "geometry Candidate boundary drifted")
    require(contract.get("stableBaseline") == "1.1.0", "geometry Stable baseline drifted")
    rules = contract.get("rules", {})
    require(rules.get("purposeSpecificCurvature") is True, "purpose-specific curvature rule missing")
    require(rules.get("uniformRoundingProhibited") is True, "uniform-rounding prohibition missing")
    require(rules.get("outerNormallyGteNested") is True and rules.get("innerFollowsOuterContour") is True, "nested-radius rules missing")
    require(rules.get("pillReservedForPillSemantics") is True, "pill semantic boundary missing")
    require(rules.get("geometryIntroducesBackdropBlur") is False, "geometry layer may not introduce blur")
    expected_tokens = {
        "checkbox": 7, "compact": 10, "control": 12, "field": 14, "floatingControl": 16,
        "surface": 20, "panel": 24, "signature": 26, "sheet": 28, "pill": 999,
    }
    require(contract.get("calibrationPx") == expected_tokens, "geometry calibration drifted")
    require(tokens.get("radiusPx") == expected_tokens, "geometry token map drifted")
    require(tokens.get("consumerEligible") is False and tokens.get("stableBaseline") == "1.1.0", "geometry token lifecycle drifted")
    impl = contract.get("implementation", {})
    require(impl.get("tokens") == "tokens/glaze-v1.2-geometry.candidate.json", "geometry token binding drifted")
    require(impl.get("webLayer") == "css/glaze-v1.2-geometry.candidate.css", "geometry CSS binding drifted")
    require(impl.get("reference") == REFERENCE, "geometry reference binding drifted")
    require(impl.get("renderedValidator") == "scripts/validate_glaze_v1_2_geometry_rendered.py", "geometry validator binding drifted")
    css = CSS.read_text(encoding="utf-8")
    require("blur(" not in css.lower(), "geometry CSS must not introduce backdrop blur")
    for marker in (
        "--glz12-radius-checkbox: 7px",
        "--glz12-radius-control: 12px",
        "--glz12-radius-surface: 20px",
        "--glz12-radius-sheet: 28px",
        "--glz12-radius-pill: 999px",
        ".glz1-morph-card[aria-expanded=\"true\"]",
        "[data-glz-text-scale=\"200\"]",
    ):
        require(marker in css, f"geometry CSS marker missing: {marker}")
    entry = ENTRYPOINT.read_text(encoding="utf-8")
    chain = [
        '@import url("./glaze-v1.2-spatial-foundation.candidate.css")',
        '@import url("./glaze-v1.2-geometry.candidate.css")',
        '@import url("./glaze-v1.2-accessibility.candidate.css")',
    ]
    require(all(item in entry for item in chain), "Candidate entrypoint missing geometry import chain")
    require([entry.index(item) for item in chain] == sorted(entry.index(item) for item in chain), "geometry/accessibility import order drifted")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    require("validate_glaze_v1_2_geometry_rendered.py" in workflow, "geometry workflow does not invoke rendered validator")
    require("github.event.pull_request.head.sha || github.sha" in workflow, "geometry workflow is not exact-head pinned")

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
            "--no-first-run", "--window-size=1280,1000",
        ]},
    }}}, timeout=60)
    require(isinstance(value, dict) and isinstance(value.get("sessionId"), str), "Chrome returned no session id")
    return value["sessionId"]

def execute(sid: str, script: str) -> Any:
    return request("POST", f"/session/{sid}/execute/sync", {"script": script, "args": []})

def cdp(sid: str, cmd: str, params: dict[str, Any] | None = None) -> Any:
    return request("POST", f"/session/{sid}/goog/cdp/execute", {"cmd": cmd, "params": params or {}})

def viewport(sid: str, width: int, height: int) -> None:
    cdp(sid, "Emulation.setDeviceMetricsOverride", {
        "width": width, "height": height, "deviceScaleFactor": 1, "mobile": False,
        "screenWidth": width, "screenHeight": height,
    })

def media(sid: str, features: list[dict[str, str]]) -> None:
    cdp(sid, "Emulation.setEmulatedMedia", {"media": "screen", "features": features})

def navigate(sid: str) -> None:
    request("POST", f"/session/{sid}/url", {"url": f"{SERVER}/{REFERENCE}"})
    end = time.monotonic() + 15
    while time.monotonic() < end:
        if execute(sid, "return document.readyState") == "complete":
            return
        time.sleep(.1)
    raise AcceptanceError("geometry reference did not finish loading")

def screenshot(sid: str, name: str) -> None:
    encoded = request("GET", f"/session/{sid}/screenshot")
    require(isinstance(encoded, str) and encoded, "no screenshot bytes")
    ARTIFACTS.mkdir(exist_ok=True)
    path = ARTIFACTS / f"glaze-v1.2-geometry-{name}.png"
    path.write_bytes(base64.b64decode(encoded))
    require(path.stat().st_size > 7000, f"invalid screenshot {path}")

STATE_JS = r"""
const ids = %s;
const radii = {};
for (const id of ids) {
  const el = document.getElementById(id);
  radii[id] = el ? parseFloat(getComputedStyle(el).borderTopLeftRadius) : null;
}
const targets = [...document.querySelectorAll('.glz12-spatial-action')].map(el => {
  const r = el.getBoundingClientRect(); return {w:r.width,h:r.height};
});
return {
  ready: document.readyState,
  width: innerWidth,
  scrollWidth: document.documentElement.scrollWidth,
  appearance: document.documentElement.dataset.glzAppearance,
  dir: document.documentElement.dir || 'ltr',
  radii,
  targets
};
""" % json.dumps(list(EXPECTED))

def state(sid: str) -> dict[str, Any]:
    value = execute(sid, STATE_JS)
    require(isinstance(value, dict), f"could not read geometry state: {value!r}")
    return value

def validate_expected(s: dict[str, Any], expected: dict[str, int] = EXPECTED) -> None:
    require(s.get("ready") == "complete", f"page not ready: {s}")
    radii = s.get("radii", {})
    for name, target in expected.items():
        actual = radii.get(name)
        require(isinstance(actual, (int, float)) and abs(float(actual) - target) < .2, f"{name} radius expected {target}, got {actual}")
    distinct = {round(float(radii[name])) for name in expected if name not in {"card-button", "sheet-button", "dock-item", "popover-field", "menu-item"}}
    require(len(distinct) >= 8, f"geometry collapsed toward uniform rounding: {sorted(distinct)}")
    require(radii["card"] >= radii["card-button"], "card nested radius hierarchy inverted")
    require(radii["popover"] >= radii["popover-field"], "popover nested radius hierarchy inverted")
    require(radii["dock"] >= radii["dock-item"], "dock nested radius hierarchy inverted")
    require(radii["sheet"] >= radii["sheet-button"], "sheet nested radius hierarchy inverted")
    require(radii["button-xs"] < radii["button"] < radii["button-xl"], "button optical-size curvature ladder drifted")
    require(radii["capsule"] > radii["capsule-expanded"], "capsule state geometry no longer transforms pill to panel")
    require(radii["morph"] < radii["morph-expanded"], "MorphCard expansion no longer increases curvature")
    require(all(float(t.get("w", 0)) >= 48 and float(t.get("h", 0)) >= 48 for t in s.get("targets", [])), f"48 px target floor drifted: {s.get('targets')}")

def require_no_overflow(s: dict[str, Any]) -> None:
    width = int(s.get("width", 0))
    require(int(s.get("scrollWidth", width + 2)) <= width + 1, f"horizontal overflow: {s}")

def main() -> int:
    http = driver = None
    sid: str | None = None
    try:
        validate_source()
        ARTIFACTS.mkdir(exist_ok=True)
        http = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(WEB_PORT), "--bind", HOST, "--directory", str(ROOT)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        wait_http(f"{SERVER}/{REFERENCE}")
        driver = subprocess.Popen(
            [chromedriver(), f"--port={DRIVER_PORT}", "--allowed-ips=127.0.0.1"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        wait_driver()
        sid = session()
        media(sid, [])
        viewport(sid, 1280, 1000)
        navigate(sid)

        for appearance in ("light", "dark", "deep-dark"):
            execute(sid, f"document.documentElement.dataset.glzAppearance='{appearance}'; return true;")
            current = state(sid)
            validate_expected(current)
            require_no_overflow(current)
            screenshot(sid, appearance)

        execute(sid, "document.documentElement.dataset.glzTransparency='reduced'; return true;")
        reduced = state(sid)
        validate_expected(reduced)
        require_no_overflow(reduced)
        execute(sid, "delete document.documentElement.dataset.glzTransparency; return true;")

        execute(sid, "document.documentElement.dir='rtl'; return true;")
        rtl = state(sid)
        validate_expected(rtl)
        require_no_overflow(rtl)
        execute(sid, "document.documentElement.dir=''; return true;")

        media(sid, [{"name": "forced-colors", "value": "active"}])
        forced = state(sid)
        validate_expected(forced)
        require_no_overflow(forced)
        screenshot(sid, "forced-colors")
        media(sid, [])

        viewport(sid, 390, 900)
        execute(sid, "document.documentElement.dataset.glzTextScale='200'; document.documentElement.style.fontSize='200%'; document.documentElement.dataset.glzAppearance='light'; return true;")
        large = state(sid)
        require_no_overflow(large)
        require(all(float(t.get("w", 0)) >= 48 and float(t.get("h", 0)) >= 48 for t in large.get("targets", [])), f"large-text target floor drifted: {large.get('targets')}")
        require(abs(float(large["radii"]["capsule"]) - 24) < .2, f"large-text capsule did not recompose to panel geometry: {large['radii']['capsule']}")
        screenshot(sid, "compact-200-text")

        print("GLAZE UI V1.2 geometry rendered web Candidate acceptance: PASS")
        print("Evidence: purpose-specific radii, nested hierarchy, optical-size/state curvature, Light/Dark/Deep Dark, Reduced Transparency, Forced Colors, RTL, 200% compact reflow, and 48 px targets.")
        print("Boundary: bounded web Candidate geometry calibration only; V1.1 remains Stable and V1.2 remains non-consumer-eligible.")
        return 0
    except AcceptanceError as error:
        print(f"GLAZE UI V1.2 geometry rendered validation failed: {error}", file=sys.stderr)
        return 1
    finally:
        if sid:
            try:
                request("DELETE", f"/session/{sid}", timeout=5)
            except Exception:
                pass
        for process in (driver, http):
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

if __name__ == "__main__":
    raise SystemExit(main())

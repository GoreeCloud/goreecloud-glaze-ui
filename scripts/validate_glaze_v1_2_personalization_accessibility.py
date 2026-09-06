#!/usr/bin/env python3
"""Bounded machine-observable accessibility checks for V1.2 Personalization."""
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
HOST, WEB_PORT, DRIVER_PORT = "127.0.0.1", 8814, 9564
SERVER, DRIVER = f"http://{HOST}:{WEB_PORT}", f"http://{HOST}:{DRIVER_PORT}"
REFERENCE = "reference/v1.2/personalization-appearance.html"
CONTRACT = ROOT / "contracts/v1.2/personalization-appearance.candidate.json"
ACCESSIBILITY = ROOT / "css/glaze-v1.2-accessibility.candidate.css"
PERSONALIZATION_CSS = ROOT / "css/glaze-v1.2-personalization-appearance.candidate.css"


class AcceptanceError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AcceptanceError(message)


def load_json(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected object in {path.relative_to(ROOT)}")
    return value


def revision() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def validate_source() -> None:
    for path in (CONTRACT, ACCESSIBILITY, PERSONALIZATION_CSS, ROOT / REFERENCE):
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    contract = load_json(CONTRACT)
    require(contract.get("version") == "1.2.0-candidate" and contract.get("lifecycle") == "candidate" and contract.get("consumerEligible") is False, "Personalization Candidate boundary drifted")
    require(contract.get("stableBaseline") == "1.1.0", "Personalization Stable baseline drifted")
    overrides = contract.get("accessibilityOverrides", {})
    for key in (
        "reducedTransparencyOverridesAtmosphere",
        "reducedTransparencyOverridesClarity",
        "increasedContrastOverridesDecorativeBoundaryStrength",
        "forcedColorsOverridesAccentRendering",
        "largeTextMayRelaxDensity",
        "touchAssistanceRaisesHitAreaFloor",
    ):
        require(overrides.get(key) is True, f"Personalization accessibility precedence drifted: {key}")
    not_established = set(contract.get("evidenceBoundary", {}).get("notEstablished", []))
    require({"assistive-technology-acceptance", "native-platform-parity", "physical-device-acceptance", "stable"}.issubset(not_established), "Personalization accessibility evidence overclaimed acceptance")

    accessibility = ACCESSIBILITY.read_text(encoding="utf-8")
    require('data-glz-touch-assistance="true"' in accessibility and "--glz12-shell-target-assisted" in accessibility, "canonical Touch Assistance authority missing")
    require('data-glz-text-scale="200"' in accessibility, "canonical Large Text authority missing")
    require('@media (forced-colors: active)' in accessibility, "canonical Forced Colors authority missing")
    require('data-glz-contrast="increased"' in accessibility and 'data-glz-boundaries="show"' in accessibility, "canonical Increased Contrast authority missing")

    css = PERSONALIZATION_CSS.read_text(encoding="utf-8")
    require('data-glz-transparency="reduced"' in css and "background-image: none !important" in css, "Personalization Reduced Transparency precedence missing")
    require('@media (forced-colors: active)' in css, "Personalization Forced Colors binding missing")


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
    while time.monotonic() < end:
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except Exception:
            pass
        time.sleep(.15)
    raise AcceptanceError(f"HTTP endpoint not ready: {url}")


def chromedriver() -> str:
    for item in (shutil.which("chromedriver"), "/usr/bin/chromedriver", "/usr/local/share/chromedriver-linux64/chromedriver"):
        if item and Path(item).is_file():
            return str(item)
    raise AcceptanceError("chromedriver unavailable")


def wait_driver() -> None:
    end = time.monotonic() + 15
    while time.monotonic() < end:
        try:
            status = request("GET", "/status")
            if isinstance(status, dict) and status.get("ready"):
                return
        except Exception:
            pass
        time.sleep(.2)
    raise AcceptanceError("chromedriver not ready")


def session() -> str:
    value = request("POST", "/session", {"capabilities": {"alwaysMatch": {"browserName": "chrome", "goog:chromeOptions": {"args": ["--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-background-networking", "--disable-component-update", "--disable-extensions", "--disable-sync", "--no-first-run", "--window-size=900,1000"]}}}}, 60)
    require(isinstance(value, dict) and isinstance(value.get("sessionId"), str), "Chrome returned no session id")
    return value["sessionId"]


def execute(sid: str, script: str) -> Any:
    return request("POST", f"/session/{sid}/execute/sync", {"script": script, "args": []})


def cdp(sid: str, cmd: str, params: dict[str, Any] | None = None) -> Any:
    return request("POST", f"/session/{sid}/goog/cdp/execute", {"cmd": cmd, "params": params or {}})


def screenshot(sid: str, name: str) -> str:
    encoded = request("GET", f"/session/{sid}/screenshot")
    require(isinstance(encoded, str) and encoded, f"no screenshot bytes for {name}")
    path = ARTIFACTS / f"glaze-v1.2-personalization-accessibility-{name}.png"
    path.write_bytes(base64.b64decode(encoded))
    require(path.stat().st_size > 4000, f"invalid screenshot {path}")
    return path.name


def ax_button_names(sid: str) -> set[str]:
    cdp(sid, "Accessibility.enable")
    tree = cdp(sid, "Accessibility.getFullAXTree")
    require(isinstance(tree, dict) and isinstance(tree.get("nodes"), list), "Chrome accessibility tree unavailable")
    names: set[str] = set()
    for node in tree["nodes"]:
        role = node.get("role", {}).get("value") if isinstance(node.get("role"), dict) else None
        name = node.get("name", {}).get("value") if isinstance(node.get("name"), dict) else None
        if str(role).lower() == "button" and isinstance(name, str) and name:
            names.add(name)
    return names


def run() -> dict[str, Any]:
    validate_source()
    ARTIFACTS.mkdir(exist_ok=True)
    http = subprocess.Popen([sys.executable, "-m", "http.server", str(WEB_PORT), "--bind", HOST, "--directory", str(ROOT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    driver = subprocess.Popen([chromedriver(), f"--port={DRIVER_PORT}", "--allowed-ips=127.0.0.1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sid: str | None = None
    try:
        wait_http(f"{SERVER}/{REFERENCE}")
        wait_driver()
        sid = session()
        request("POST", f"/session/{sid}/url", {"url": f"{SERVER}/{REFERENCE}"})
        end = time.monotonic() + 15
        while time.monotonic() < end:
            if execute(sid, "return document.readyState==='complete' && window.personalizationReady===true"):
                break
            time.sleep(.1)
        else:
            raise AcceptanceError("Personalization reference not ready")

        base = execute(sid, """const a=document.getElementById('action').getBoundingClientRect(),w=document.getElementById('semantic-warning');return {action:{w:a.width,h:a.height},warningText:w.textContent.trim(),expression:getComputedStyle(document.getElementById('expression')).backgroundImage};""")
        require(base["action"]["w"] >= 48 and base["action"]["h"] >= 48, "Personalization action fell below default 48px target floor")
        require("Security review required" in base["warningText"], "protected semantic warning content missing")

        names = ax_button_names(sid)
        required_names = {"Follow System", "Light", "Dark", "Deep Dark", "Clear", "Balanced", "Dense", "Personalization action"}
        require(required_names.issubset(names), f"Personalization accessible button names drifted: missing {sorted(required_names - names)}")

        execute(sid, "document.documentElement.dataset.glzTouchAssistance='true';return true;")
        assisted = execute(sid, "const a=document.getElementById('action').getBoundingClientRect();return {w:a.width,h:a.height};")
        require(assisted["w"] >= 56 and assisted["h"] >= 56, f"Touch Assistance did not raise Personalization action to 56px: {assisted}")
        assisted_shot = screenshot(sid, "touch-assistance")
        execute(sid, "delete document.documentElement.dataset.glzTouchAssistance;return true;")

        execute(sid, "window.glazePersonalizationReference.applyWallpaperAtmosphere(document,{r:255,g:0,b:96});document.documentElement.dataset.glzTransparency='reduced';return true;")
        reduced = execute(sid, "const s=getComputedStyle(document.getElementById('expression'));return {background:s.backgroundImage,wallpaper:document.documentElement.dataset.glzWallpaperAtmosphere||null};")
        require(reduced["background"] == "none", f"Reduced Transparency did not suppress Personalization/wallpaper atmosphere: {reduced}")
        require(reduced["wallpaper"] == "local-bounded", "wallpaper source state unexpectedly disappeared rather than being visually overridden")
        execute(sid, "delete document.documentElement.dataset.glzTransparency;return true;")

        execute(sid, "document.documentElement.dataset.glzContrast='increased';document.documentElement.dataset.glzBoundaries='show';return true;")
        contrast = execute(sid, "const w=getComputedStyle(document.getElementById('semantic-warning')),a=getComputedStyle(document.getElementById('action'));return {warningBorder:parseFloat(w.borderTopWidth),actionBorder:parseFloat(a.borderTopWidth)};")
        require(contrast["warningBorder"] >= 2 and contrast["actionBorder"] >= 2, f"Increased Contrast did not strengthen functional/semantic boundaries: {contrast}")
        execute(sid, "delete document.documentElement.dataset.glzContrast;delete document.documentElement.dataset.glzBoundaries;return true;")

        cdp(sid, "Emulation.setDeviceMetricsOverride", {"width": 320, "height": 1200, "deviceScaleFactor": 1, "mobile": False, "screenWidth": 320, "screenHeight": 1200})
        execute(sid, "document.documentElement.dataset.glzTextScale='200';document.documentElement.style.fontSize='200%';window.glazePersonalizationReference.controller.set({density:'productive'});return true;")
        large = execute(sid, "const a=document.getElementById('action').getBoundingClientRect();return {scroll:document.documentElement.scrollWidth,inner:innerWidth,actionHeight:a.height,columns:getComputedStyle(document.getElementById('personal-grid')).gridTemplateColumns};")
        require(large["scroll"] <= large["inner"] + 1, f"200% compact Personalization caused page overflow: {large}")
        require(large["actionHeight"] >= 48, "200% compact Personalization weakened action target floor")
        require(" " not in str(large["columns"]).strip(), f"200% Personalization did not reflow to one column: {large}")
        large_shot = screenshot(sid, "compact-200")
        execute(sid, "delete document.documentElement.dataset.glzTextScale;document.documentElement.style.fontSize='';return true;")

        cdp(sid, "Emulation.setEmulatedMedia", {"media": "screen", "features": [{"name": "forced-colors", "value": "active"}]})
        forced = execute(sid, "const e=getComputedStyle(document.getElementById('expression')),a=getComputedStyle(document.getElementById('accent-card'));return {active:matchMedia('(forced-colors: active)').matches,expressionBackground:e.backgroundImage,accentBackground:a.backgroundImage,accentForced:a.forcedColorAdjust};")
        require(forced["active"] is True, "Forced Colors emulation failed")
        require(forced["expressionBackground"] == "none" and forced["accentBackground"] == "none", f"Forced Colors did not remove decorative Personalization atmosphere: {forced}")
        forced_shot = screenshot(sid, "forced-colors")

        return {
            "sourceRevision": revision(),
            "status": "passed",
            "defaultTarget": base["action"],
            "accessibleButtonNames": sorted(names),
            "touchAssistance": assisted,
            "reducedTransparency": reduced,
            "increasedContrast": contrast,
            "compact200": large,
            "forcedColors": forced,
            "screenshots": [assisted_shot, large_shot, forced_shot],
            "assistiveTechnologyAcceptance": False,
            "physicalDeviceAccessibilityAcceptance": False,
            "nativePlatformAccessibilityParity": False,
        }
    finally:
        if sid:
            try:
                request("DELETE", f"/session/{sid}", timeout=5)
            except Exception:
                pass
        for process in (driver, http):
            process.terminate()
            try:
                process.wait(timeout=5)
            except Exception:
                process.kill()


def main() -> int:
    ARTIFACTS.mkdir(exist_ok=True)
    output = ARTIFACTS / "glaze-v1.2-personalization-accessibility-evidence.json"
    evidence: dict[str, Any] = {"sourceRevision": revision(), "status": "started"}
    output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    try:
        evidence = run()
        output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print("PASS: V1.2 Personalization machine-observable accessibility integration passed; assistive-technology/native/physical-device acceptance remains open.")
        return 0
    except Exception as error:
        evidence["status"] = "failed"
        evidence["error"] = str(error)
        output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print(f"V1.2 Personalization accessibility integration failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

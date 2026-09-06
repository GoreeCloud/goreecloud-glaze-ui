#!/usr/bin/env python3
"""Rendered web acceptance for the GLAZE UI V1.2 Frosted Optical foundation.

This gate validates the Candidate optical implementation only. Passing it does not
promote V1.2, establish native-platform support, or make any consumer eligible.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
HOST = "127.0.0.1"
WEB_PORT = 8784
DRIVER_PORT = 9534
SERVER_BASE = f"http://{HOST}:{WEB_PORT}"
DRIVER_BASE = f"http://{HOST}:{DRIVER_PORT}"
REFERENCE = "reference/v1.2/optical-foundation.html"
TOKEN_PATH = ROOT / "tokens/glaze-v1.2-optical-foundation.candidate.json"
OPTICAL_CSS_PATH = ROOT / "css/glaze-v1.2-optical.candidate.css"
ENTRYPOINT_PATH = ROOT / "css/glaze-v1.2.0-candidate.css"
REFERENCE_PATH = ROOT / REFERENCE


class AcceptanceError(RuntimeError):
    pass


def require(value: bool, message: str) -> None:
    if not value:
        raise AcceptanceError(message)


def validate_source_contract() -> None:
    for path in (TOKEN_PATH, OPTICAL_CSS_PATH, ENTRYPOINT_PATH, REFERENCE_PATH):
        require(path.is_file(), f"missing required optical implementation file: {path.relative_to(ROOT)}")

    token = json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
    require(token.get("implementationStatus") == "candidate-web-optical-layer", "optical implementation status drifted")
    bindings = token.get("implementationBindings", {})
    require(bindings.get("webLayer") == "css/glaze-v1.2-optical.candidate.css", "webLayer binding drifted")
    require(bindings.get("webEntrypoint") == "css/glaze-v1.2.0-candidate.css", "webEntrypoint binding drifted")
    require(bindings.get("reference") == REFERENCE, "optical reference binding drifted")
    require(bindings.get("renderedValidator") == "scripts/validate_glaze_v1_2_optical_rendered.py", "rendered validator binding drifted")

    aura_policy = token.get("auraPolicy", {})
    require(
        aura_policy.get("legacyV11TealAmberAuraFields") == "retired-in-v1.2-web-optical-layer",
        "legacy V1.1 Aura retirement status drifted",
    )

    css = OPTICAL_CSS_PATH.read_text(encoding="utf-8")
    for marker in (
        "--glz12-frost-white: #F4F8FA",
        "--glz12-ice-blue: #DCECF6",
        "--glz12-cool-graphite: #151C22",
        "--glz12-blue-black: #070C11",
        '--glz11-aura-teal-max: transparent',
        '--glz11-aura-amber-max: transparent',
        'data-glz-frost="clear"',
        'data-glz-frost="mist"',
        'data-glz-frost="frost"',
        'data-glz-frost="dense-frost"',
        'data-glz-frost="opaque-frost"',
        'data-glz-material-performance="reduced"',
        'data-glz-material-performance="minimal"',
        ".glz1-universal-search",
    ):
        require(marker in css, f"optical CSS missing required marker {marker!r}")

    entrypoint = ENTRYPOINT_PATH.read_text(encoding="utf-8")
    neutral = '@import url("./glaze-v1.2-frosted-neutral.candidate.css")'
    components = '@import url("./glaze-v1.2-components.candidate.css")'
    shell = '@import url("./glaze-v1.2-system-shell.candidate.css")'
    optical = '@import url("./glaze-v1.2-optical.candidate.css")'
    accessibility = '@import url("./glaze-v1.2-accessibility.candidate.css")'
    for marker in (neutral, components, shell, optical, accessibility):
        require(marker in entrypoint, f"Candidate entrypoint missing {marker}")
    require(
        entrypoint.index(neutral) < entrypoint.index(components) < entrypoint.index(shell) < entrypoint.index(optical) < entrypoint.index(accessibility),
        "Candidate optical import must follow component/System Shell mappings and precede accessibility overrides",
    )


def request(method: str, path: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> Any:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = Request(
        f"{DRIVER_BASE}{path}",
        data=body,
        method=method,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise AcceptanceError(f"WebDriver HTTP {error.code} for {path}: {detail}") from error
    except (URLError, TimeoutError) as error:
        raise AcceptanceError(f"WebDriver request failed for {path}: {error}") from error
    if not raw:
        return None
    value = json.loads(raw.decode("utf-8")).get("value")
    if isinstance(value, dict) and value.get("error"):
        raise AcceptanceError(f"WebDriver {value.get('error')}: {value.get('message', '')}")
    return value


def wait_http(url: str, seconds: float = 15) -> None:
    deadline = time.monotonic() + seconds
    last: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except Exception as error:
            last = error
        time.sleep(0.15)
    raise AcceptanceError(f"HTTP endpoint did not become ready: {url}: {last}")


def chromedriver() -> str:
    for candidate in (
        shutil.which("chromedriver"),
        "/usr/bin/chromedriver",
        "/usr/local/share/chromedriver-linux64/chromedriver",
    ):
        if candidate and Path(candidate).is_file():
            return str(candidate)
    raise AcceptanceError("chromedriver is unavailable on the runner")


def wait_driver() -> None:
    deadline = time.monotonic() + 15
    last: Exception | None = None
    while time.monotonic() < deadline:
        try:
            state = request("GET", "/status")
            if isinstance(state, dict) and state.get("ready"):
                return
        except Exception as error:
            last = error
        time.sleep(0.2)
    raise AcceptanceError(f"chromedriver did not become ready: {last}")


def create_session() -> str:
    value = request(
        "POST",
        "/session",
        {
            "capabilities": {
                "alwaysMatch": {
                    "browserName": "chrome",
                    "goog:chromeOptions": {
                        "args": [
                            "--headless=new",
                            "--no-sandbox",
                            "--disable-dev-shm-usage",
                            "--disable-background-networking",
                            "--disable-component-update",
                            "--disable-default-apps",
                            "--disable-extensions",
                            "--disable-sync",
                            "--metrics-recording-only",
                            "--no-first-run",
                            "--window-size=1440,1000",
                        ]
                    },
                }
            }
        },
        timeout=60,
    )
    require(isinstance(value, dict), f"Unexpected Chrome session response: {value!r}")
    session_id = value.get("sessionId")
    require(isinstance(session_id, str) and session_id, "Chrome did not return a session id")
    return session_id


def execute(session_id: str, script: str) -> Any:
    return request("POST", f"/session/{session_id}/execute/sync", {"script": script, "args": []})


def cdp(session_id: str, command: str, params: dict[str, Any] | None = None) -> Any:
    return request("POST", f"/session/{session_id}/goog/cdp/execute", {"cmd": command, "params": params or {}})


def set_viewport(session_id: str, width: int, height: int, mobile: bool = False) -> None:
    cdp(
        session_id,
        "Emulation.setDeviceMetricsOverride",
        {
            "width": width,
            "height": height,
            "deviceScaleFactor": 1,
            "mobile": mobile,
            "screenWidth": width,
            "screenHeight": height,
        },
    )


def emulate_media(session_id: str, features: list[dict[str, str]]) -> None:
    cdp(session_id, "Emulation.setEmulatedMedia", {"media": "screen", "features": features})


def navigate(session_id: str) -> None:
    request("POST", f"/session/{session_id}/url", {"url": f"{SERVER_BASE}/{REFERENCE}"})
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if execute(session_id, "return document.readyState") == "complete":
            return
        time.sleep(0.1)
    raise AcceptanceError(f"Page did not finish loading: {REFERENCE}")


def screenshot(session_id: str, name: str) -> Path:
    encoded = request("GET", f"/session/{session_id}/screenshot")
    require(isinstance(encoded, str) and encoded, f"Chrome did not return screenshot bytes for {name}")
    ARTIFACTS.mkdir(exist_ok=True)
    path = ARTIFACTS / f"glaze-v1.2-optical-{name}.png"
    path.write_bytes(base64.b64decode(encoded))
    require(path.stat().st_size > 8_000, f"Screenshot appears empty or invalid: {path}")
    return path


def blur_px(value: str) -> float:
    if value in {"none", ""}:
        return 0.0
    match = re.search(r"blur\(([\d.]+)px\)", value)
    require(match is not None, f"Expected blur() in rendered filter: {value!r}")
    assert match is not None
    return float(match.group(1))


def state(session_id: str) -> dict[str, Any]:
    value = execute(
        session_id,
        r"""
        const root=document.documentElement;
        const rs=getComputedStyle(root);
        const q=s=>document.querySelector(s);
        const cs=e=>e?getComputedStyle(e):null;
        const filter=e=>{const s=cs(e);return s?(s.backdropFilter||s.webkitBackdropFilter||'none'):'missing'};
        const entry=q('.glz1-universal-search .glz1-search-entry');
        const panel=q('.glz1-universal-search .glz1-search-panel');
        const result=q('.glz1-universal-search .glz1-search-result[aria-selected="true"]');
        const reading=q('.reading-card');
        const stage=q('.glz12-optical-stage');
        const selectedStyle=cs(result);
        const entryStyle=cs(entry);
        const panelStyle=cs(panel);
        const readingStyle=cs(reading);
        const stageBefore=getComputedStyle(stage,'::before');
        const localAura=getComputedStyle(q('[data-glz-optical-aura="ice"]'),'::after');
        const rootRect=document.documentElement.getBoundingClientRect();
        return {
          ready:document.readyState,
          width:innerWidth,
          scrollWidth:document.documentElement.scrollWidth,
          version:root.getAttribute('data-glaze-version'),
          upgrade:root.getAttribute('data-glaze-upgrade'),
          appearance:root.getAttribute('data-glz-appearance'),
          profile:root.getAttribute('data-glz-material-performance'),
          frostWhite:rs.getPropertyValue('--glz12-frost-white').trim(),
          crystalWhite:rs.getPropertyValue('--glz12-crystal-white').trim(),
          iceBlue:rs.getPropertyValue('--glz12-ice-blue').trim(),
          cloudGray:rs.getPropertyValue('--glz12-cloud-gray').trim(),
          coolGraphite:rs.getPropertyValue('--glz12-cool-graphite').trim(),
          blueBlack:rs.getPropertyValue('--glz12-blue-black').trim(),
          legacyTealAura:rs.getPropertyValue('--glz11-aura-teal-max').trim(),
          legacyAmberAura:rs.getPropertyValue('--glz11-aura-amber-max').trim(),
          materialProfile:rs.getPropertyValue('--glz12-material-profile').trim(),
          auraOpacity:parseFloat(rs.getPropertyValue('--glz12-aura-opacity')) || 0,
          stageAuraOpacity:parseFloat(stageBefore.opacity) || 0,
          localAuraOpacity:parseFloat(localAura.opacity) || 0,
          entryFilter:filter(entry),
          panelFilter:filter(panel),
          resultFilter:filter(result),
          readingFilter:filter(reading),
          entryBackground:entryStyle&&entryStyle.backgroundColor,
          panelBackground:panelStyle&&panelStyle.backgroundColor,
          resultBackground:selectedStyle&&selectedStyle.backgroundColor,
          readingBackground:readingStyle&&readingStyle.backgroundColor,
          entryShadow:entryStyle&&entryStyle.boxShadow,
          panelShadow:panelStyle&&panelStyle.boxShadow,
          rootWidth:rootRect.width
        };
        """,
    )
    require(isinstance(value, dict), f"Could not read optical state: {value!r}")
    return value


def validate_identity(s: dict[str, Any], width: int) -> None:
    require(s.get("ready") == "complete", "optical reference did not finish loading")
    require(abs(int(s.get("width", 0)) - width) <= 1, f"viewport width mismatch: {s}")
    require(int(s.get("scrollWidth", width + 2)) <= width + 1, f"horizontal overflow: {s}")
    require(s.get("version") == "1.1", "V1.1 Stable baseline marker is missing")
    require(s.get("upgrade") == "v1.2-frosted-neutral", "V1.2 Candidate activation marker is missing")
    expected = {
        "frostWhite": "#F4F8FA",
        "crystalWhite": "#FBFDFE",
        "iceBlue": "#DCECF6",
        "cloudGray": "#DCE3E8",
        "coolGraphite": "#151C22",
        "blueBlack": "#070C11",
    }
    for key, target in expected.items():
        require(str(s.get(key, "")).upper() == target, f"{key} optical role drifted: {s.get(key)!r}")
    require(s.get("legacyTealAura") == "transparent", f"legacy teal Aura is still active: {s}")
    require(s.get("legacyAmberAura") == "transparent", f"legacy amber Aura is still active: {s}")
    require(s.get("resultFilter") == "none", f"search result added nested blur: {s}")
    require(s.get("readingFilter") == "none", f"durable reading surface must not use backdrop blur: {s}")


def validate_full(s: dict[str, Any]) -> tuple[float, float]:
    require(s.get("profile") == "full" and s.get("materialProfile") == "full", f"Full profile is not active: {s}")
    entry = blur_px(str(s.get("entryFilter")))
    panel = blur_px(str(s.get("panelFilter")))
    require(entry >= 27.5, f"Full Search Frost is below reference blur: {s}")
    require(panel >= 43.5, f"Full Search Dense Frost is below reference blur: {s}")
    require(panel > entry, f"Search panel must be denser than entry in Full profile: {s}")
    require(float(s.get("auraOpacity", 0)) >= 0.99, f"Full Aura is unexpectedly attenuated: {s}")
    require(float(s.get("stageAuraOpacity", 0)) >= 0.99, f"Rendered Full Aura field is unexpectedly attenuated: {s}")
    require(float(s.get("localAuraOpacity", 0)) >= 0.70, f"Full local Ice Aura is unexpectedly attenuated: {s}")
    return entry, panel


def set_profile(session_id: str, profile: str) -> dict[str, Any]:
    execute(session_id, f"document.documentElement.setAttribute('data-glz-material-performance','{profile}');return true;")
    return state(session_id)


def validate_reduced(s: dict[str, Any], full_entry: float, full_panel: float) -> None:
    require(s.get("profile") == "reduced" and s.get("materialProfile") == "reduced", f"Reduced profile is not active: {s}")
    entry = blur_px(str(s.get("entryFilter")))
    panel = blur_px(str(s.get("panelFilter")))
    require(0 < entry < full_entry, f"Reduced profile did not lower Search entry blur: {s}")
    require(0 < panel < full_panel, f"Reduced profile did not lower Search panel blur: {s}")
    require(0.25 <= float(s.get("auraOpacity", 0)) <= 0.6, f"Reduced Aura attenuation drifted: {s}")
    require(0.15 <= float(s.get("localAuraOpacity", 0)) <= 0.4, f"Reduced local Aura attenuation drifted: {s}")


def validate_minimal(s: dict[str, Any]) -> None:
    require(s.get("profile") == "minimal" and s.get("materialProfile") == "minimal", f"Minimal profile is not active: {s}")
    require(s.get("entryFilter") == "none", f"Minimal profile must remove Search entry blur: {s}")
    require(s.get("panelFilter") == "none", f"Minimal profile must remove Search panel blur: {s}")
    require(float(s.get("auraOpacity", 1)) == 0, f"Minimal profile must disable Aura: {s}")
    require(float(s.get("stageAuraOpacity", 1)) == 0, f"Rendered Minimal Aura field must be hidden: {s}")
    require(float(s.get("localAuraOpacity", 1)) == 0, f"Minimal local Aura must be hidden: {s}")


def validate_reduced_transparency(session_id: str) -> None:
    execute(session_id, "document.documentElement.setAttribute('data-glz-material-performance','full');document.documentElement.setAttribute('data-glz-transparency','reduced');return true;")
    s = state(session_id)
    require(s.get("entryFilter") == "none" and s.get("panelFilter") == "none", f"Reduced Transparency must remove Search blur: {s}")
    require(float(s.get("auraOpacity", 1)) == 0, f"Reduced Transparency must disable Aura: {s}")
    require(float(s.get("localAuraOpacity", 1)) == 0, f"Reduced Transparency must disable local Aura: {s}")
    screenshot(session_id, "reduced-transparency")
    execute(session_id, "document.documentElement.removeAttribute('data-glz-transparency');return true;")


def validate_forced_colors(session_id: str) -> None:
    emulate_media(session_id, [{"name": "forced-colors", "value": "active"}])
    s = state(session_id)
    require(s.get("entryFilter") == "none" and s.get("panelFilter") == "none", f"Forced Colors must remove Search blur: {s}")
    require(float(s.get("auraOpacity", 1)) == 0, f"Forced Colors must disable Aura: {s}")
    require(float(s.get("localAuraOpacity", 1)) == 0, f"Forced Colors must disable local Aura: {s}")
    require(s.get("entryShadow") == "none" and s.get("panelShadow") == "none", f"Forced Colors must remove custom Search shadows: {s}")
    screenshot(session_id, "forced-colors")
    emulate_media(session_id, [])


def validate_200_text(session_id: str, width: int) -> None:
    execute(session_id, "document.documentElement.style.fontSize='200%';return true;")
    s = state(session_id)
    require(int(s.get("scrollWidth", width + 2)) <= width + 1, f"200% text creates horizontal overflow: {s}")
    execute(session_id, "document.documentElement.style.fontSize='';return true;")


def main() -> int:
    http_process: subprocess.Popen[str] | None = None
    driver_process: subprocess.Popen[str] | None = None
    session_id: str | None = None
    try:
        validate_source_contract()
        ARTIFACTS.mkdir(exist_ok=True)
        http_process = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(WEB_PORT), "--bind", HOST, "--directory", str(ROOT)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        wait_http(f"{SERVER_BASE}/{REFERENCE}")
        driver_process = subprocess.Popen(
            [chromedriver(), f"--port={DRIVER_PORT}", "--allowed-ips=127.0.0.1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        wait_driver()
        session_id = create_session()

        set_viewport(session_id, 1440, 1000)
        emulate_media(session_id, [])
        navigate(session_id)
        light = state(session_id)
        validate_identity(light, 1440)
        full_entry, full_panel = validate_full(light)
        screenshot(session_id, "light-full")

        reduced = set_profile(session_id, "reduced")
        validate_identity(reduced, 1440)
        validate_reduced(reduced, full_entry, full_panel)
        screenshot(session_id, "light-reduced")

        minimal = set_profile(session_id, "minimal")
        validate_identity(minimal, 1440)
        validate_minimal(minimal)
        screenshot(session_id, "light-minimal")

        execute(session_id, "document.documentElement.setAttribute('data-glz-material-performance','full');document.documentElement.setAttribute('data-glz-appearance','dark');return true;")
        dark = state(session_id)
        validate_identity(dark, 1440)
        validate_full(dark)
        screenshot(session_id, "dark-full")

        execute(session_id, "document.documentElement.setAttribute('data-glz-appearance','deep-dark');return true;")
        deep = state(session_id)
        validate_identity(deep, 1440)
        validate_full(deep)
        screenshot(session_id, "deep-dark-full")

        execute(session_id, "document.documentElement.setAttribute('data-glz-appearance','light');return true;")
        validate_reduced_transparency(session_id)
        validate_forced_colors(session_id)
        validate_200_text(session_id, 1440)

        set_viewport(session_id, 390, 844, mobile=True)
        navigate(session_id)
        mobile = state(session_id)
        validate_identity(mobile, 390)
        validate_full(mobile)
        screenshot(session_id, "mobile-full")

        print("GLAZE UI V1.2 Frosted Optical rendered web Candidate acceptance: PASS")
        print("Evidence: Full/Reduced/Minimal profiles, Light/Dark/Deep Dark, Reduced Transparency, Forced Colors, 200% text, and mobile.")
        print("Boundary: web Candidate optical evidence only; V1.1 remains Stable and V1.2 remains non-consumer-eligible.")
        return 0
    except AcceptanceError as error:
        print(f"GLAZE UI V1.2 Frosted Optical rendered acceptance failed: {error}", file=sys.stderr)
        return 1
    finally:
        if session_id:
            try:
                request("DELETE", f"/session/{session_id}", timeout=5)
            except Exception:
                pass
        for process in (driver_process, http_process):
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()


if __name__ == "__main__":
    raise SystemExit(main())

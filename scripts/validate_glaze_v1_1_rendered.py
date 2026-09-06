#!/usr/bin/env python3
"""Rendered acceptance for the isolated GLAZE UI V1.1 candidate.

Uses a real Chromium-class browser through ChromeDriver, validates the exact
checked-out revision at desktop/tablet/mobile viewports, exercises required
accessibility fallbacks and input states, and writes reviewable screenshots.
Passing this gate is rendered web evidence only; it is not human optical,
native-platform, release, consumer, or production acceptance.
"""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
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
WEB_PORT = 8781
DRIVER_PORT = 9531
SERVER_BASE = f"http://{HOST}:{WEB_PORT}"
DRIVER_BASE = f"http://{HOST}:{DRIVER_PORT}"
ENTRYPOINT = "glaze-v1.1.0-candidate.css"
TAB_KEY = "\ue004"

SCENES = (
    ("desktop-workspace", "reference/v1.1/desktop-workspace.html", 1440, 1000, False, "dark", "#0b0d11"),
    ("tablet-dashboard", "reference/v1.1/tablet-dashboard.html", 1024, 820, False, "deep-dark", "#05070a"),
    ("mobile-application", "reference/v1.1/mobile-application.html", 390, 844, True, "light", "#f5f7fa"),
)


class RenderedAcceptanceError(RuntimeError):
    pass


def require(value: bool, message: str) -> None:
    if not value:
        raise RenderedAcceptanceError(message)


def request(method: str, path: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> Any:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = Request(f"{DRIVER_BASE}{path}", data=body, method=method, headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RenderedAcceptanceError(f"WebDriver HTTP {error.code} for {path}: {detail}") from error
    except (URLError, TimeoutError) as error:
        raise RenderedAcceptanceError(f"WebDriver request failed for {path}: {error}") from error
    if not raw:
        return None
    value = json.loads(raw.decode("utf-8")).get("value")
    if isinstance(value, dict) and value.get("error"):
        raise RenderedAcceptanceError(f"WebDriver {value.get('error')}: {value.get('message', '')}")
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
    raise RenderedAcceptanceError(f"HTTP endpoint did not become ready: {url}: {last}")


def chromedriver() -> str:
    for candidate in (shutil.which("chromedriver"), "/usr/bin/chromedriver", "/usr/local/share/chromedriver-linux64/chromedriver"):
        if candidate and Path(candidate).is_file():
            return str(candidate)
    raise RenderedAcceptanceError("chromedriver is unavailable on the runner")


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
    raise RenderedAcceptanceError(f"chromedriver did not become ready: {last}")


def create_session() -> str:
    value = request("POST", "/session", {"capabilities": {"alwaysMatch": {"browserName": "chrome", "goog:chromeOptions": {"args": ["--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-background-networking", "--disable-component-update", "--disable-default-apps", "--disable-extensions", "--disable-sync", "--metrics-recording-only", "--no-first-run", "--window-size=1440,1000"]}}}})
    require(isinstance(value, dict), f"Unexpected Chrome session response: {value!r}")
    session_id = value.get("sessionId")
    require(isinstance(session_id, str) and bool(session_id), "Chrome did not return a session id")
    return session_id


def execute(session_id: str, script: str) -> Any:
    return request("POST", f"/session/{session_id}/execute/sync", {"script": script, "args": []})


def execute_async(session_id: str, script: str) -> Any:
    return request("POST", f"/session/{session_id}/execute/async", {"script": script, "args": []})


def cdp(session_id: str, command: str, params: dict[str, Any] | None = None) -> Any:
    return request("POST", f"/session/{session_id}/goog/cdp/execute", {"cmd": command, "params": params or {}})


def send_tab(session_id: str) -> None:
    request("POST", f"/session/{session_id}/actions", {"actions": [{"type": "key", "id": "keyboard", "actions": [{"type": "keyDown", "value": TAB_KEY}, {"type": "keyUp", "value": TAB_KEY}]}]})


def set_viewport(session_id: str, width: int, height: int, mobile: bool) -> None:
    cdp(session_id, "Emulation.setDeviceMetricsOverride", {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": mobile, "screenWidth": width, "screenHeight": height})
    cdp(session_id, "Emulation.setTouchEmulationEnabled", {"enabled": mobile, "maxTouchPoints": 5 if mobile else 1})


def emulate_media(session_id: str, features: list[dict[str, str]]) -> None:
    cdp(session_id, "Emulation.setEmulatedMedia", {"media": "screen", "features": features})


def navigate(session_id: str, relative: str) -> None:
    request("POST", f"/session/{session_id}/url", {"url": f"{SERVER_BASE}/{relative}"})
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if execute(session_id, "return document.readyState") == "complete":
            return
        time.sleep(0.1)
    raise RenderedAcceptanceError(f"Page did not finish loading: {relative}")


def settle_render(session_id: str) -> None:
    state = execute_async(session_id, r"""
        const done = arguments[arguments.length - 1];
        const complete = () => {
          window.scrollTo(0, 0);
          void document.documentElement.getBoundingClientRect();
          requestAnimationFrame(() => requestAnimationFrame(() => requestAnimationFrame(() => {
            done({
              ready: document.readyState,
              fonts: document.fonts ? document.fonts.status : 'unsupported'
            });
          })));
        };
        if (document.fonts && document.fonts.ready) {
          document.fonts.ready.then(complete, complete);
        } else {
          complete();
        }
    """)
    require(isinstance(state, dict) and state.get("ready") == "complete", f"render did not settle on a complete document: {state}")
    require(state.get("fonts") in {"loaded", "unsupported"}, f"render fonts did not settle: {state}")


def capture_png(session_id: str, name: str) -> bytes:
    encoded = request("GET", f"/session/{session_id}/screenshot")
    require(isinstance(encoded, str) and bool(encoded), f"Chrome did not return screenshot bytes for {name}")
    image = base64.b64decode(encoded)
    require(len(image) > 10_000, f"Screenshot appears empty or invalid for {name}")
    return image


def screenshot(session_id: str, name: str) -> Path:
    settle_render(session_id)
    first = capture_png(session_id, name)
    settle_render(session_id)
    second = capture_png(session_id, name)
    first_hash = hashlib.sha256(first).hexdigest()
    second_hash = hashlib.sha256(second).hexdigest()
    require(
        first == second,
        f"Screenshot capture is nondeterministic for {name}: first={first_hash}, second={second_hash}",
    )
    ARTIFACTS.mkdir(exist_ok=True)
    path = ARTIFACTS / f"glaze-v1.1-{name}.png"
    path.write_bytes(second)
    return path


def read_state(session_id: str) -> dict[str, Any]:
    value = execute(session_id, r"""
        const q=s=>document.querySelector(s);
        const root=document.documentElement;
        const scene=q('[data-glz11-scene]');
        const header=q('.glz11-reference-header');
        const hero=q('.glz11-hero');
        const rootStyle=getComputedStyle(root);
        const active=document.activeElement;
        const activeStyle=active?getComputedStyle(active):null;
        const visibleControls=[...document.querySelectorAll('.glz11-button,.glz11-nav-item,.glz11-field')]
          .map(el=>({el,r:el.getBoundingClientRect()})).filter(x=>x.r.width>0&&x.r.height>0)
          .map(x=>({tag:x.el.tagName,height:x.r.height,width:x.r.width,text:(x.el.textContent||x.el.getAttribute('aria-label')||'').trim()}));
        const before=getComputedStyle(scene,'::before');
        const after=getComputedStyle(scene,'::after');
        const headerStyle=header?getComputedStyle(header):null;
        const heroStyle=hero?getComputedStyle(hero):null;
        const links=[...document.styleSheets].map(s=>s.href||'').filter(Boolean);
        return {
          ready:document.readyState,width:innerWidth,height:innerHeight,
          scrollWidth:document.documentElement.scrollWidth,scrollHeight:document.documentElement.scrollHeight,
          candidate:root.getAttribute('data-glaze-version-candidate'),appearance:root.getAttribute('data-glz-appearance'),
          scene:scene&&scene.getAttribute('data-glz11-scene'),dir:root.dir||rootStyle.direction,
          rootFont:parseFloat(rootStyle.fontSize),canvasRole:rootStyle.getPropertyValue('--glz1-canvas').trim().toLowerCase(),
          baseRole:rootStyle.getPropertyValue('--glz1-base').trim().toLowerCase(),scripts:document.querySelectorAll('script').length,
          controls:visibleControls,beforeDisplay:before.display,afterDisplay:after.display,
          beforeBackground:before.backgroundImage,afterBackground:after.backgroundImage,
          headerBackground:headerStyle&&headerStyle.backgroundImage,headerBoxShadow:headerStyle&&headerStyle.boxShadow,
          headerBorderWidth:headerStyle&&headerStyle.borderTopWidth,heroBorderWidth:heroStyle&&heroStyle.borderTopWidth,
          activeTag:active&&active.tagName,activeText:active&&(active.textContent||active.getAttribute('aria-label')||'').trim(),
          activeOutlineWidth:activeStyle&&activeStyle.outlineWidth,activeOutlineStyle:activeStyle&&activeStyle.outlineStyle,
          stylesheets:links,
        };
    """)
    require(isinstance(value, dict), f"Could not read rendered state: {value!r}")
    return value


def validate_normal(state: dict[str, Any], scene: str, width: int, appearance: str, expected_canvas: str) -> None:
    require(state.get("ready") == "complete", f"{scene}: document is not complete")
    require(abs(int(state.get("width", 0)) - width) <= 1, f"{scene}: viewport width mismatch: {state}")
    require(int(state.get("scrollWidth", width + 2)) <= width + 1, f"{scene}: horizontal overflow: {state}")
    require(state.get("candidate") == "1.1", f"{scene}: candidate activation is missing")
    require(state.get("appearance") == appearance, f"{scene}: expected {appearance} appearance: {state}")
    require(state.get("scene") == scene, f"{scene}: reference family marker mismatch")
    require(int(state.get("scripts", 1)) == 0, f"{scene}: reference must remain script-free")
    require(any(ENTRYPOINT in href for href in state.get("stylesheets", [])), f"{scene}: versioned candidate entrypoint is not active")
    require(state.get("canvasRole") == expected_canvas, f"{scene}: explicit {appearance} appearance adapter did not resolve V1 canvas role: {state.get('canvasRole')}")
    require(bool(state.get("baseRole")), f"{scene}: explicit appearance adapter did not resolve V1 base role")
    require(state.get("beforeDisplay") != "none" and state.get("afterDisplay") != "none", f"{scene}: canonical two-field atmosphere is not rendered")
    require(state.get("beforeBackground") != "none" and state.get("afterBackground") != "none", f"{scene}: atmosphere fields have no rendered background")
    controls = state.get("controls") or []
    require(bool(controls), f"{scene}: no visible candidate controls found")
    require(not [c for c in controls if float(c.get("height", 0)) < 47.5], f"{scene}: visible control below 48px floor: {controls}")


def validate_keyboard_focus(session_id: str, scene: str) -> None:
    execute(session_id, "document.activeElement && document.activeElement.blur(); return true;")
    send_tab(session_id)
    state = read_state(session_id)
    require(state.get("activeTag") in {"A", "BUTTON", "INPUT"}, f"{scene}: Tab did not reach an interactive control: {state}")
    require(state.get("activeOutlineStyle") != "none", f"{scene}: keyboard focus has no visible outline: {state}")
    width = float(str(state.get("activeOutlineWidth") or "0").replace("px", ""))
    require(width >= 2.5, f"{scene}: keyboard focus outline is weaker than V1 reference expectation: {state}")


def validate_touch_assistance(session_id: str, scene: str) -> None:
    execute(session_id, "document.documentElement.setAttribute('data-glz-touch-assistance','true');return true;")
    state = read_state(session_id)
    controls = state.get("controls") or []
    require(not [c for c in controls if float(c.get("height", 0)) < 55.5], f"{scene}: Touch Assistance control below 56px floor: {controls}")
    execute(session_id, "document.documentElement.removeAttribute('data-glz-touch-assistance');return true;")


def validate_reduced_transparency(session_id: str, scene: str) -> None:
    execute(session_id, "document.documentElement.setAttribute('data-glz-transparency','reduced'); return true;")
    state = read_state(session_id)
    require(state.get("beforeDisplay") == "none" and state.get("afterDisplay") == "none", f"{scene}: Reduced Transparency did not suppress Aura fields")
    require(state.get("headerBackground") == "none", f"{scene}: Reduced Transparency did not remove candidate header tint")
    execute(session_id, "document.documentElement.removeAttribute('data-glz-transparency'); return true;")


def validate_increased_contrast(session_id: str, scene: str) -> None:
    execute(session_id, "document.documentElement.setAttribute('data-mode','increased-contrast'); return true;")
    state = read_state(session_id)
    require(state.get("beforeDisplay") == "none" and state.get("afterDisplay") == "none", f"{scene}: Increased Contrast did not suppress Aura fields")
    width = float(str(state.get("headerBorderWidth") or "0").replace("px", ""))
    require(width >= 1.9, f"{scene}: Increased Contrast did not strengthen visible boundaries: {state}")
    execute(session_id, "document.documentElement.removeAttribute('data-mode'); return true;")


def validate_200_rtl(session_id: str, scene: str, width: int) -> None:
    execute(session_id, "document.documentElement.style.fontSize='200%';document.documentElement.dir='rtl';return true;")
    state = read_state(session_id)
    require(float(state.get("rootFont", 0)) >= 31.5, f"{scene}: 200% root text scaling is not active")
    require(state.get("dir") == "rtl", f"{scene}: RTL direction is not active")
    require(int(state.get("scrollWidth", width + 2)) <= width + 1, f"{scene}: 200%/RTL creates root horizontal overflow: {state}")
    execute(session_id, "document.documentElement.style.fontSize='';document.documentElement.dir='';return true;")


def validate_reduced_motion(session_id: str, scene: str) -> None:
    emulate_media(session_id, [{"name": "prefers-reduced-motion", "value": "reduce"}])
    result = execute(session_id, "return {before:getComputedStyle(document.querySelector('[data-glz11-scene]'),'::before').animationName,after:getComputedStyle(document.querySelector('[data-glz11-scene]'),'::after').animationName};")
    require(isinstance(result, dict) and result.get("before") == "none" and result.get("after") == "none", f"{scene}: Reduced Motion must have no atmospheric animation: {result}")
    emulate_media(session_id, [])


def validate_forced_colors(session_id: str, scene: str) -> None:
    emulate_media(session_id, [{"name": "forced-colors", "value": "active"}])
    state = read_state(session_id)
    require(state.get("beforeDisplay") == "none" and state.get("afterDisplay") == "none", f"{scene}: Forced Colors did not suppress Aura fields")
    require(state.get("headerBackground") == "none", f"{scene}: Forced Colors did not remove custom atmospheric header background")
    require(state.get("headerBoxShadow") == "none", f"{scene}: Forced Colors did not remove custom optical shadow")
    emulate_media(session_id, [])


def main() -> int:
    http_process: subprocess.Popen[str] | None = None
    driver_process: subprocess.Popen[str] | None = None
    session_id: str | None = None
    try:
        ARTIFACTS.mkdir(exist_ok=True)
        http_process = subprocess.Popen([sys.executable, "-m", "http.server", str(WEB_PORT), "--bind", HOST, "--directory", str(ROOT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
        wait_http(f"{SERVER_BASE}/reference/v1.1/desktop-workspace.html")
        driver_process = subprocess.Popen([chromedriver(), f"--port={DRIVER_PORT}", "--allowed-ips=127.0.0.1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
        wait_driver()
        session_id = create_session()

        for scene, relative, width, height, mobile, appearance, expected_canvas in SCENES:
            set_viewport(session_id, width, height, mobile)
            emulate_media(session_id, [])
            navigate(session_id, relative)
            cdp(session_id, "Emulation.setScrollbarsHidden", {"hidden": mobile})
            validate_normal(read_state(session_id), scene, width, appearance, expected_canvas)
            validate_keyboard_focus(session_id, scene)
            screenshot(session_id, scene)
            validate_touch_assistance(session_id, scene)
            validate_reduced_transparency(session_id, scene)
            if scene == "desktop-workspace":
                execute(session_id, "document.documentElement.setAttribute('data-glz-transparency','reduced');return true;")
                screenshot(session_id, "desktop-reduced-transparency")
                execute(session_id, "document.documentElement.removeAttribute('data-glz-transparency');return true;")
            validate_increased_contrast(session_id, scene)
            validate_reduced_motion(session_id, scene)
            validate_forced_colors(session_id, scene)
            if scene == "desktop-workspace":
                emulate_media(session_id, [{"name": "forced-colors", "value": "active"}])
                screenshot(session_id, "desktop-forced-colors")
                emulate_media(session_id, [])
            validate_200_rtl(session_id, scene, width)

        print("GLAZE UI V1.1 rendered web candidate acceptance: PASS")
        print("Evidence: desktop/tablet/mobile plus reduced-transparency and forced-colors screenshots written to artifacts/.")
        print("Coverage: appearance roles, 48/56px targets, keyboard focus, Increased Contrast, Reduced Transparency, Reduced Motion, Forced Colors, 200% text, RTL, touch and pointer-form-factor rendering.")
        print("Boundary: rendered web evidence only; human optical/native/release/production acceptance remains separate.")
        return 0
    except Exception as error:
        print(f"GLAZE UI V1.1 rendered candidate acceptance FAILED: {error}")
        return 1
    finally:
        if session_id:
            try:
                request("DELETE", f"/session/{session_id}")
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
    sys.exit(main())
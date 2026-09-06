#!/usr/bin/env python3
"""Bounded rendered-web acceptance for GLAZE UI V1.2 Candidate typography."""
from __future__ import annotations

import base64, json, shutil, subprocess, sys, time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
HOST = "127.0.0.1"
WEB_PORT = 8787
DRIVER_PORT = 9537
SERVER = f"http://{HOST}:{WEB_PORT}"
DRIVER = f"http://{HOST}:{DRIVER_PORT}"
REFERENCE = "reference/v1.2/typography.html"
CONTRACT = ROOT / "contracts/v1.2/typography.candidate.json"
TOKENS = ROOT / "tokens/glaze-v1.2-typography.candidate.json"
CSS = ROOT / "css/glaze-v1.2-typography.candidate.css"
ENTRYPOINT = ROOT / "css/glaze-v1.2.0-candidate.css"
ROLES = {"Display", "LargeTitle", "Title", "Heading", "Subheading", "Body", "UI", "Label", "Caption", "Numeric", "Monospace"}

class AcceptanceError(RuntimeError):
    pass

def require(ok: bool, message: str) -> None:
    if not ok:
        raise AcceptanceError(message)

def validate_source() -> None:
    for path in (CONTRACT, TOKENS, CSS, ENTRYPOINT, ROOT / REFERENCE):
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    tokens = json.loads(TOKENS.read_text(encoding="utf-8"))
    require(contract.get("version") == "1.2.0-candidate", "typography contract version drifted")
    require(contract.get("lifecycle") == "candidate" and contract.get("consumerEligible") is False, "Candidate lifecycle boundary drifted")
    require(contract.get("stableBaseline") == "1.1.0", "Stable baseline drifted")
    require(set(contract.get("roles", {})) == ROLES, "semantic typography role coverage drifted")
    require(contract.get("sourcePolicy", {}).get("thirdPartyRuntimeFontDeliveryAllowed") is False, "remote runtime font policy drifted")
    require(contract.get("metrics", {}).get("minimumTextScalePercent") == 200, "large-text gate drifted")
    require(contract.get("sharpText", {}).get("blurAllowed") is False, "sharp-text blur prohibition drifted")
    impl = contract.get("implementation", {})
    require(impl.get("tokens") == "tokens/glaze-v1.2-typography.candidate.json", "token binding drifted")
    require(impl.get("webLayer") == "css/glaze-v1.2-typography.candidate.css", "CSS binding drifted")
    require(impl.get("reference") == REFERENCE, "reference binding drifted")
    require(impl.get("renderedValidator") == "scripts/validate_glaze_v1_2_typography_rendered.py", "validator binding drifted")
    expected = {"display", "largeTitle", "title", "heading", "subheading", "body", "ui", "label", "caption", "numeric", "monospace"}
    require(set(tokens.get("roles", {})) == expected, "typography token role coverage drifted")
    family = tokens.get("family", {})
    require(str(family.get("sans", "")).startswith("system-ui"), "Candidate sans stack must stay system-native first")
    require("ui-monospace" in str(family.get("monospace", "")), "Candidate monospace stack missing native-first family")
    require(tokens.get("rules", {}).get("remoteRuntimeFontDependencyAllowed") is False, "runtime font dependency policy drifted")
    text = (CSS.read_text(encoding="utf-8") + "\n" + (ROOT / REFERENCE).read_text(encoding="utf-8")).lower()
    for marker in ("data-glz-type=\"display\"", "data-glz-type=\"numeric\"", "data-glz-type=\"monospace\"", ".glz12-type-icon-label", "font-variant-numeric: tabular-nums", "@media (forced-colors: active)"):
        require(marker in text, f"typography implementation marker missing: {marker}")
    for forbidden in ("fonts.googleapis.com", "fonts.gstatic.com", "use.typekit.net", "fonts.adobe.com", "@font-face"):
        require(forbidden not in text, f"forbidden runtime font source found: {forbidden}")
    entry = ENTRYPOINT.read_text(encoding="utf-8")
    chain = [
        '@import url("./glaze-v1.2-chrome-optics.candidate.css")',
        '@import url("./glaze-v1.2-legacy-aura-retirement.candidate.css")',
        '@import url("./glaze-v1.2-typography.candidate.css")',
        '@import url("./glaze-v1.2-accessibility.candidate.css")',
    ]
    require(all(item in entry for item in chain), "Candidate entrypoint missing typography import chain")
    require([entry.index(item) for item in chain] == sorted(entry.index(item) for item in chain), "typography/accessibility import order drifted")

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
            status = request("GET", "/status")
            if isinstance(status, dict) and status.get("ready"):
                return
        except Exception as error:
            last = error
        time.sleep(.2)
    raise AcceptanceError(f"chromedriver not ready: {last}")

def session() -> str:
    value = request("POST", "/session", {"capabilities": {"alwaysMatch": {"browserName": "chrome", "goog:chromeOptions": {"args": ["--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-background-networking", "--disable-component-update", "--disable-extensions", "--disable-sync", "--metrics-recording-only", "--no-first-run", "--window-size=1280,960"]}}}}, timeout=60)
    require(isinstance(value, dict) and isinstance(value.get("sessionId"), str), "Chrome returned no session id")
    return value["sessionId"]

def execute(sid: str, script: str) -> Any:
    return request("POST", f"/session/{sid}/execute/sync", {"script": script, "args": []})

def cdp(sid: str, cmd: str, params: dict[str, Any] | None = None) -> Any:
    return request("POST", f"/session/{sid}/goog/cdp/execute", {"cmd": cmd, "params": params or {}})

def viewport(sid: str, width: int, height: int, mobile: bool = False) -> None:
    cdp(sid, "Emulation.setDeviceMetricsOverride", {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": mobile, "screenWidth": width, "screenHeight": height})

def media(sid: str, features: list[dict[str, str]]) -> None:
    cdp(sid, "Emulation.setEmulatedMedia", {"media": "screen", "features": features})

def navigate(sid: str) -> None:
    request("POST", f"/session/{sid}/url", {"url": f"{SERVER}/{REFERENCE}"})
    end = time.monotonic() + 15
    while time.monotonic() < end:
        if execute(sid, "return document.readyState") == "complete":
            return
        time.sleep(.1)
    raise AcceptanceError("typography reference did not finish loading")

def screenshot(sid: str, name: str) -> None:
    encoded = request("GET", f"/session/{sid}/screenshot")
    require(isinstance(encoded, str) and encoded, "no screenshot bytes")
    ARTIFACTS.mkdir(exist_ok=True)
    path = ARTIFACTS / f"glaze-v1.2-typography-{name}.png"
    path.write_bytes(base64.b64decode(encoded))
    require(path.stat().st_size > 7000, f"invalid screenshot {path}")

STATE_JS = r'''
const root=document.documentElement;
const r=s=>{const e=document.querySelector(s),c=e&&getComputedStyle(e);return c?{size:parseFloat(c.fontSize),line:parseFloat(c.lineHeight),weight:c.fontWeight,letter:c.letterSpacing,family:c.fontFamily,color:c.color,shadow:c.textShadow,filter:c.filter,numeric:c.fontVariantNumeric,ligatures:c.fontVariantLigatures}:null};
const align=document.querySelector('.glz12-type-icon-label'), ac=getComputedStyle(align), svg=align.querySelector('svg'), sc=getComputedStyle(svg);
return {ready:document.readyState,width:innerWidth,scrollWidth:document.documentElement.scrollWidth,version:root.dataset.glazeVersion,upgrade:root.dataset.glazeUpgrade,appearance:root.dataset.glzAppearance,
 display:r('[data-glz-type="display"]'),largeTitle:r('[data-glz-type="large-title"]'),title:r('[data-glz-type="title"]'),heading:r('[data-glz-type="heading"]'),subheading:r('[data-glz-type="subheading"]'),body:r('[data-glz-type="body"]'),ui:r('[data-glz-type="ui"]'),label:r('[data-glz-type="label"]'),caption:r('[data-glz-type="caption"]'),numeric:r('[data-glz-type="numeric"]'),mono:r('[data-glz-type="monospace"]'),
 align:{display:ac.display,alignItems:ac.alignItems,gap:parseFloat(ac.columnGap),svgW:parseFloat(sc.width),svgH:parseFloat(sc.height)}};'''

def state(sid: str) -> dict[str, Any]:
    value = execute(sid, STATE_JS)
    require(isinstance(value, dict), f"could not read typography state: {value!r}")
    return value

def validate_state(s: dict[str, Any], width: int) -> None:
    require(s.get("ready") == "complete" and abs(int(s.get("width", 0)) - width) <= 1, f"page/viewport mismatch: {s}")
    require(int(s.get("scrollWidth", width + 2)) <= width + 1, f"horizontal overflow: {s}")
    require(s.get("version") == "1.1" and s.get("upgrade") == "v1.2-frosted-neutral", "Candidate activation boundary missing")
    sizes = [s[k]["size"] for k in ("display", "largeTitle", "title", "heading", "subheading", "body", "ui", "label", "caption")]
    require(all(a > b for a, b in zip(sizes, sizes[1:])), f"semantic size ladder drifted: {sizes}")
    require(abs(s["body"]["size"] - 16) < .2, f"body size drifted: {s['body']}")
    require(float(s["body"]["line"]) > float(s["body"]["size"]) * 1.45, f"body line height too tight: {s['body']}")
    require("system-ui" in s["body"]["family"].lower(), f"system-native sans stack inactive: {s['body']}")
    require("monospace" in s["mono"]["family"].lower() or "consolas" in s["mono"]["family"].lower(), f"monospace stack inactive: {s['mono']}")
    require("tabular-nums" in s["numeric"]["numeric"], f"tabular numerals inactive: {s['numeric']}")
    require(s["mono"]["ligatures"] in ("none", "no-common-ligatures"), f"technical ligatures not disabled: {s['mono']}")
    for key in ("display", "body", "ui", "numeric", "mono"):
        require(s[key]["shadow"] == "none" and s[key]["filter"] == "none", f"sharp-text rule violated for {key}: {s[key]}")
    a = s["align"]
    require(a["display"] in ("flex", "inline-flex") and a["alignItems"] == "center", f"icon-label alignment primitive drifted: {a}")
    require(7.5 <= a["gap"] <= 8.5 and 19.5 <= a["svgW"] <= 20.5 and 19.5 <= a["svgH"] <= 20.5, f"icon-label optical metrics drifted: {a}")

def set_appearance(sid: str, appearance: str) -> dict[str, Any]:
    execute(sid, f"document.documentElement.setAttribute('data-glz-appearance','{appearance}');return true;")
    return state(sid)

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
        viewport(sid, 1280, 960)
        media(sid, [])
        navigate(sid)
        for appearance in ("light", "dark", "deep-dark"):
            s = set_appearance(sid, appearance)
            validate_state(s, 1280)
            screenshot(sid, appearance)
        viewport(sid, 390, 844, True)
        execute(sid, "document.documentElement.style.fontSize='200%';document.documentElement.setAttribute('data-glz-appearance','light');return true;")
        large = state(sid)
        require(int(large.get("scrollWidth", 392)) <= 391, f"200% mobile text overflow: {large}")
        require(large["body"]["size"] >= 31.5, f"200% text scaling did not apply: {large['body']}")
        screenshot(sid, "mobile-200-percent")
        execute(sid, "document.documentElement.style.fontSize='';return true;")
        viewport(sid, 1280, 960)
        media(sid, [{"name": "forced-colors", "value": "active"}])
        forced = state(sid)
        for key in ("display", "body", "ui", "numeric", "mono"):
            require(forced[key]["shadow"] == "none" and forced[key]["filter"] == "none", f"Forced Colors sharp-text rule violated for {key}: {forced[key]}")
        screenshot(sid, "forced-colors")
        print("GLAZE UI V1.2 Candidate typography rendered validation passed.")
        return 0
    except Exception as error:
        print(f"GLAZE UI V1.2 Candidate typography rendered validation failed: {error}", file=sys.stderr)
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

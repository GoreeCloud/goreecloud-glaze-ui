#!/usr/bin/env python3
"""Rendered acceptance for bounded GLAZE UI V1.2 Accessibility Adaptation combinations."""
from __future__ import annotations

import base64
import json
import re
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
WEB_PORT = 8801
DRIVER_PORT = 9551
SERVER = f"http://{HOST}:{WEB_PORT}"
DRIVER = f"http://{HOST}:{DRIVER_PORT}"
REFERENCE = "reference/v1.2/accessibility-adaptation.html"
CONTRACT = ROOT / "contracts/v1.2/accessibility-adaptation.candidate.json"
MATRIX = ROOT / "contracts/accessibility/resolution-matrix.json"
CSS = ROOT / "css/glaze-v1.2-accessibility.candidate.css"
ENTRYPOINT = ROOT / "css/glaze-v1.2.0-candidate.css"
WORKFLOW = ROOT / ".github/workflows/glaze-v1.2-accessibility-adaptation.yml"
EXPECTED_ORDER = [
    "protected-semantic-meaning", "forced-colors", "reduced-motion", "reduced-transparency",
    "increased-contrast-and-show-boundaries", "large-text-and-touch-assistance",
    "material-clarity", "expression-and-accent",
]
EXPECTED_CASES = ["rt-clear", "rm-expressive", "fc-accent", "large-compact", "touch-compact", "contrast-boundaries"]


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
    for path in (CONTRACT, MATRIX, CSS, ENTRYPOINT, WORKFLOW, ROOT / REFERENCE):
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    contract = load(CONTRACT)
    matrix = load(MATRIX)
    require(contract.get("version") == "1.2.0-candidate", "accessibility contract version drifted")
    require(contract.get("lifecycle") == "candidate" and contract.get("consumerEligible") is False, "accessibility Candidate boundary drifted")
    require(contract.get("stableBaseline") == "1.1.0", "accessibility Stable baseline drifted")
    require(contract.get("resolutionOrder") == EXPECTED_ORDER == matrix.get("resolutionOrder"), "accessibility resolution order drifted")
    require(contract.get("canonicalCases") == matrix.get("testCases"), "accessibility canonical case copy drifted from authority")
    require([case.get("id") for case in contract.get("canonicalCases", [])] == EXPECTED_CASES, "accessibility case order/set drifted")
    require(matrix.get("visualReview", {}).get("required") is True, "canonical human visual-review requirement disappeared")
    rules = contract.get("rules", {})
    for key in ("finalAccessibilityCascadeResolvesCompatibility", "reducedMotionPreservesDirectManipulation", "reducedTransparencyForcesSolidMaterial", "largeTextRequiresReflow", "touchAssistanceRaisesHitFloorWithoutRequiringVisibleGeometryInflation", "forcedColorsUsesPlatformRoles", "consumerClaimBlocked"):
        require(rules.get(key) is True, f"accessibility rule drifted: {key}")
    for key in ("canonicalResolutionMatrixCopiedAsAuthority", "protectedSemanticsMayBeOverriddenByPersonalization", "reducedMotionMayOnlySpeedUpOriginalMotion", "automatedEvidenceEstablishesHumanAcceptance", "automatedEvidenceEstablishesAssistiveTechnologyAcceptance", "automatedEvidenceEstablishesNativePlatformAcceptance"):
        require(rules.get(key) is False, f"accessibility fail-closed rule drifted: {key}")
    not_established = set(contract.get("evidenceBoundary", {}).get("notEstablished", []))
    require({"human-visual-review", "screen-reader-acceptance", "talkback-acceptance", "voiceover-acceptance", "complete-native-platform-accessibility-parity", "stable"}.issubset(not_established), "accessibility evidence boundary overclaims acceptance")
    acceptance = contract.get("acceptance", {})
    require(acceptance.get("canonicalCaseIds") == EXPECTED_CASES, "accessibility acceptance cases drifted")
    require(acceptance.get("compactViewportPx") == 320, "accessibility compact viewport drifted")
    require(acceptance.get("minimumInteractiveTargetPx") == 48 and acceptance.get("touchAssistanceMinimumInteractiveTargetPx") == 56, "accessibility target floors drifted")
    require(acceptance.get("textScalePercent") == 200, "accessibility text scale drifted")

    css = CSS.read_text(encoding="utf-8")
    for marker in (
        'data-glz-motion="reduced"', 'data-glz-transparency="reduced"', 'data-glz-contrast="increased"',
        'data-glz-boundaries="show"', 'data-glz-text-scale="200"', 'data-glz-touch-assistance="true"',
        'data-glz-direct-manipulation="true"', '--glz12-state-focus-width-contrast', '--glz12-shell-target-assisted',
        '.glz12-a11y-scene[hidden]', '@media (forced-colors: active)',
    ):
        require(marker in css, f"accessibility CSS marker missing: {marker}")
    require("@media (max-width" not in css.lower() and "@media (min-width" not in css.lower(), "accessibility resolution layer created viewport identity authority")

    entry = ENTRYPOINT.read_text(encoding="utf-8").strip()
    require(entry.endswith('@import url("./glaze-v1.2-accessibility.candidate.css");'), "accessibility layer is not final in Candidate cascade")
    reference = (ROOT / REFERENCE).read_text(encoding="utf-8")
    cases = re.findall(r'data-a11y-case="([^"]+)"', reference)
    require(cases == EXPECTED_CASES, f"accessibility reference case order/set drifted: {cases}")
    for marker in ("Automated browser evidence does not establish human visual", "Security action required", "Direct manipulation position probe", "Configuration destination with a deliberately long readable label"):
        require(marker in reference, f"accessibility reference marker missing: {marker}")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    require("validate_glaze_v1_2_accessibility_adaptation_rendered.py" in workflow, "accessibility workflow does not run rendered validator")
    require("github.event.pull_request.head.sha || github.sha" in workflow, "accessibility workflow is not exact-head pinned")


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
            value = request("GET", "/status")
            if isinstance(value, dict) and value.get("ready"):
                return
        except Exception as error:
            last = error
        time.sleep(.2)
    raise AcceptanceError(f"chromedriver not ready: {last}")


def session() -> str:
    value = request("POST", "/session", {"capabilities": {"alwaysMatch": {"browserName": "chrome", "goog:chromeOptions": {"args": ["--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-background-networking", "--disable-component-update", "--disable-extensions", "--disable-sync", "--metrics-recording-only", "--no-first-run", "--window-size=900,1000"]}}}}, timeout=60)
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
    raise AcceptanceError("accessibility reference did not finish loading")


def isolate(sid: str, case_id: str) -> None:
    media(sid, [])
    execute(sid, f"""
const root=document.documentElement;
for(const name of ['data-glz-motion','data-glz-transparency','data-glz-contrast','data-glz-boundaries','data-glz-text-scale','data-glz-touch-assistance','data-glz-material-clarity','data-glz-expression','data-glz-accent','data-mode']) root.removeAttribute(name);
root.style.fontSize='';root.style.removeProperty('--glz1-focus');root.dir='ltr';
for(const scene of document.querySelectorAll('[data-a11y-case]')) scene.hidden=scene.dataset.a11yCase!=={json.dumps(case_id)};
return true;
""")


def screenshot(sid: str, name: str) -> None:
    encoded = request("GET", f"/session/{sid}/screenshot")
    require(isinstance(encoded, str) and encoded, "no screenshot bytes")
    ARTIFACTS.mkdir(exist_ok=True)
    path = ARTIFACTS / f"glaze-v1.2-accessibility-adaptation-{name}.png"
    path.write_bytes(base64.b64decode(encoded))
    require(path.stat().st_size > 5000, f"invalid screenshot {path}")


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
        viewport(sid, 900, 1000)
        navigate(sid)

        isolate(sid, "rt-clear")
        execute(sid, "document.documentElement.dataset.glzTransparency='reduced';document.documentElement.dataset.glzMaterialClarity='clear';return true;")
        rt = execute(sid, """const c=getComputedStyle(document.getElementById('rt-capsule'));const r=getComputedStyle(document.documentElement);const s=document.getElementById('rt-semantic').getBoundingClientRect();return {backdrop:c.backdropFilter||c.webkitBackdropFilter||'none',blur:r.getPropertyValue('--glz12-blur-standard').trim(),semanticVisible:s.width>0&&s.height>0,text:document.getElementById('rt-semantic').innerText};""")
        require(rt.get("backdrop") == "none" and rt.get("blur") == "0px", f"Reduced Transparency did not force Solid/effects-free rendering: {rt}")
        require(rt.get("semanticVisible") is True and "Warning" in rt.get("text", ""), f"protected semantic meaning disappeared under Reduced Transparency: {rt}")
        screenshot(sid, "rt-clear")

        isolate(sid, "rm-expressive")
        execute(sid, "document.documentElement.dataset.glzMotion='reduced';document.documentElement.dataset.glzExpression='expressive';return true;")
        rm = execute(sid, """const p=getComputedStyle(document.getElementById('rm-press'));const d=getComputedStyle(document.getElementById('rm-direct'));return {pressTransform:p.transform,pressTransition:p.transitionDuration,directTransform:d.transform,directTransition:d.transitionDuration};""")
        require(rm.get("pressTransform") == "none", f"Reduced Motion retained nonessential press travel: {rm}")
        require(set(str(rm.get("pressTransition", "")).split(", ")) <= {"0s"}, f"Reduced Motion merely retained/accelerated press transition: {rm}")
        require(rm.get("directTransform") not in (None, "", "none"), f"Reduced Motion broke direct manipulation tracking: {rm}")
        screenshot(sid, "rm-expressive")

        isolate(sid, "fc-accent")
        execute(sid, "document.documentElement.dataset.glzAccent='custom';document.documentElement.style.setProperty('--glz1-focus','rgb(255, 0, 255)');return true;")
        media(sid, [{"name": "forced-colors", "value": "active"}])
        fc = execute(sid, """const b=getComputedStyle(document.getElementById('fc-selected'));const s=getComputedStyle(document.getElementById('fc-protected'));const r=document.getElementById('fc-protected').getBoundingClientRect();return {forced:b.forcedColorAdjust,background:b.backgroundColor,border:b.borderColor,semanticBorder:s.borderInlineStartWidth,semanticVisible:r.width>0&&r.height>0,text:document.getElementById('fc-protected').innerText};""")
        require(fc.get("forced") == "auto", f"Forced Colors did not remain platform-authoritative: {fc}")
        require(fc.get("background") != "rgb(255, 0, 255)", f"custom accent overrode Forced Colors: {fc}")
        require(fc.get("semanticVisible") is True and "Security action required" in fc.get("text", "") and float(str(fc.get("semanticBorder", "0px")).replace("px", "") or 0) > 0, f"protected semantic structure disappeared in Forced Colors: {fc}")
        screenshot(sid, "fc-accent")

        isolate(sid, "large-compact")
        media(sid, [])
        viewport(sid, 320, 1200)
        execute(sid, "document.documentElement.dataset.glzTextScale='200';document.documentElement.style.fontSize='200%';return true;")
        large = execute(sid, """const root=getComputedStyle(document.documentElement);const label=document.getElementById('large-label');const field=document.getElementById('large-field');const action=document.getElementById('large-action');const lr=label.getBoundingClientRect(),fr=field.getBoundingClientRect(),ar=action.getBoundingClientRect();return {width:innerWidth,scrollWidth:document.documentElement.scrollWidth,font:parseFloat(root.fontSize),label:{w:lr.width,sw:label.scrollWidth,h:lr.height,sh:label.scrollHeight},field:{w:fr.width,sw:field.scrollWidth},action:{w:ar.width,h:ar.height}};""")
        require(int(large.get("scrollWidth", 9999)) <= 321, f"200% Compact page overflowed horizontally: {large}")
        require(float(large.get("font", 0)) >= 30, f"200% text was not actually exercised: {large}")
        require(float(large["label"]["sw"]) <= float(large["label"]["w"]) + 1 and float(large["label"]["sh"]) <= float(large["label"]["h"]) + 1, f"critical large-text label clipped: {large}")
        require(float(large["field"]["sw"]) <= float(large["field"]["w"]) + 1, f"large-text field clipped horizontally: {large}")
        require(float(large["action"]["w"]) >= 48 and float(large["action"]["h"]) >= 48, f"large-text action lost target floor: {large}")
        screenshot(sid, "large-compact")

        isolate(sid, "touch-compact")
        viewport(sid, 320, 900)
        execute(sid, "document.documentElement.dataset.glzTouchAssistance='true';return true;")
        touch = execute(sid, """const els=[...document.querySelectorAll('#touch-row button')];const rects=els.map(e=>{const r=e.getBoundingClientRect();return {id:e.id,l:r.left,t:r.top,r:r.right,b:r.bottom,w:r.width,h:r.height}});let overlap=false;for(let i=0;i<rects.length;i++)for(let j=i+1;j<rects.length;j++){const a=rects[i],b=rects[j];if(Math.max(a.l,b.l)<Math.min(a.r,b.r)&&Math.max(a.t,b.t)<Math.min(a.b,b.b))overlap=true;}return {rects,overlap,scrollWidth:document.documentElement.scrollWidth};""")
        require(all(float(item["w"]) >= 56 and float(item["h"]) >= 56 for item in touch.get("rects", [])), f"Touch Assistance 56px floor drifted: {touch}")
        require(touch.get("overlap") is False and int(touch.get("scrollWidth", 9999)) <= 321, f"Touch Assistance created ambiguous overlap/overflow: {touch}")
        screenshot(sid, "touch-compact")

        isolate(sid, "contrast-boundaries")
        viewport(sid, 900, 900)
        execute(sid, "document.documentElement.dataset.glzContrast='increased';document.documentElement.dataset.glzBoundaries='show';document.getElementById('contrast-focus').focus();return true;")
        contrast = execute(sid, """const s=getComputedStyle(document.getElementById('contrast-surface'));const f=getComputedStyle(document.getElementById('contrast-focus'));return {surfaceBorder:parseFloat(s.borderTopWidth)||0,focusOutline:parseFloat(f.outlineWidth)||0,focusStyle:f.outlineStyle};""")
        require(float(contrast.get("surfaceBorder", 0)) >= 3, f"Show Boundaries did not strengthen floating surface structure: {contrast}")
        require(float(contrast.get("focusOutline", 0)) >= 4 and contrast.get("focusStyle") != "none", f"Increased Contrast did not produce strong focus visibility: {contrast}")
        screenshot(sid, "contrast-boundaries")

        print("GLAZE UI V1.2 Accessibility Adaptation validated: six canonical resolution-matrix combinations PASS; human/AT/native acceptance remains explicitly unestablished")
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
        print(f"GLAZE UI V1.2 Accessibility Adaptation acceptance failed: {error}")
        raise SystemExit(1)

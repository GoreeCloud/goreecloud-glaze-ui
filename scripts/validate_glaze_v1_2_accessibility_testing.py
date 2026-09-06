#!/usr/bin/env python3
"""Bounded Phase 5 automated accessibility testing for GLAZE UI V1.2 Candidate."""
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
HOST, WEB_PORT, DRIVER_PORT = "127.0.0.1", 8804, 9554
SERVER, DRIVER = f"http://{HOST}:{WEB_PORT}", f"http://{HOST}:{DRIVER_PORT}"
CONTRACT = ROOT / "contracts/v1.2/accessibility-testing.candidate.json"
MATRIX = ROOT / "contracts/accessibility/resolution-matrix.json"
ADAPTATION = ROOT / "contracts/v1.2/accessibility-adaptation.candidate.json"
A11Y_REFERENCE = "reference/v1.2/accessibility-adaptation.html"
RESPONSIVE_REFERENCE = "reference/v1.2/responsive-adaptation.html"
DELEGATED = [
    ROOT / "scripts/validate_glaze_v1_2_accessibility_adaptation_rendered.py",
    ROOT / "scripts/validate_glaze_v1_2_responsive_adaptation_rendered.py",
]
EXPECTED_SCOPE = [
    "keyboard-navigation",
    "screen-reader-semantics-machine-observable-subset",
    "accessible-names",
    "focus-order",
    "visible-focus",
    "touch-targets",
    "text-scale-200-plus",
    "rtl",
    "reduced-motion",
    "reduced-transparency",
    "increased-contrast",
    "forced-colors",
    "grayscale",
    "color-vision-accessibility-machine-observable-subset",
    "mobile-accessibility",
    "far-view-accessibility",
    "material-readability-machine-observable-subset",
]


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


def validate_source() -> dict[str, Any]:
    for path in (CONTRACT, MATRIX, ADAPTATION, ROOT / A11Y_REFERENCE, ROOT / RESPONSIVE_REFERENCE, *DELEGATED):
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    contract = load_json(CONTRACT)
    matrix = load_json(MATRIX)
    adaptation = load_json(ADAPTATION)
    require(contract.get("version") == "1.2.0-candidate", "Accessibility Testing version drifted")
    require(contract.get("lifecycle") == "candidate" and contract.get("consumerEligible") is False, "Accessibility Testing lifecycle boundary drifted")
    require(contract.get("stableBaseline") == "1.1.0", "Accessibility Testing Stable baseline drifted")
    require(contract.get("phase") == "Phase 5 — Accessibility Testing", "Accessibility Testing phase drifted")
    require(contract.get("canonicalTaskScope") == EXPECTED_SCOPE, "Accessibility Testing scope drifted")
    require(contract.get("evidenceBoundary", {}).get("boundedAutomatedAccessibilityTestingEstablished") is True, "bounded automated evidence flag drifted")
    require(contract.get("evidenceBoundary", {}).get("phase5AccessibilityTestingComplete") is False, "automated gate may not claim full Phase 5 accessibility completion")
    rules = contract.get("rules", {})
    require(rules.get("reuseExistingAccessibilityAuthority") is True and rules.get("introduceParallelAccessibilityTokenOwner") is False, "Accessibility authority boundary drifted")
    require(rules.get("realKeyboardInputRequiredForKeyboardTraversal") is True, "real keyboard traversal requirement drifted")
    for key in (
        "browserAccessibilityTreeEqualsScreenReaderAcceptance",
        "automatedBrowserTestingEqualsHumanAcceptance",
        "automatedBrowserTestingEqualsTalkBackAcceptance",
        "automatedBrowserTestingEqualsVoiceOverAcceptance",
        "automatedBrowserTestingEqualsPhysicalDeviceAcceptance",
        "automatedBrowserTestingEqualsNativePlatformAccessibilityAcceptance",
    ):
        require(rules.get(key) is False, f"Accessibility overclaim guard drifted: {key}")
    not_established = set(contract.get("evidenceBoundary", {}).get("notEstablished", []))
    require({"screen-reader-acceptance", "talkback-acceptance", "voiceover-acceptance", "physical-device-accessibility-acceptance", "complete-native-platform-accessibility-parity", "stable"}.issubset(not_established), "Accessibility evidence boundary lost required blockers")
    require(matrix.get("visualReview", {}).get("required") is True, "canonical Accessibility visual review requirement disappeared")
    require(adaptation.get("lifecycle") == "candidate" and adaptation.get("consumerEligible") is False and adaptation.get("stableBaseline") == "1.1.0", "Accessibility Adaptation authority drifted")
    require([case.get("id") for case in matrix.get("testCases", [])] == ["rt-clear", "rm-expressive", "fc-accent", "large-compact", "touch-compact", "contrast-boundaries"], "canonical Accessibility test-case matrix drifted")
    a11y = (ROOT / A11Y_REFERENCE).read_text(encoding="utf-8")
    for marker in ('id="touch-primary"', 'id="touch-secondary"', 'id="touch-more"', 'aria-label="More options"', 'id="contrast-focus"', 'id="large-label"', 'id="fc-protected"'):
        require(marker in a11y, f"Accessibility reference marker missing: {marker}")
    responsive = (ROOT / RESPONSIVE_REFERENCE).read_text(encoding="utf-8")
    for marker in ('data-adaptation-scene="320-mobile"', 'data-adaptation-scene="tv-far-view"', 'data-adaptation-scene="rtl"', 'aria-current="page"'):
        require(marker in responsive, f"Responsive accessibility marker missing: {marker}")
    return contract


def run_delegated() -> list[str]:
    passed: list[str] = []
    for path in DELEGATED:
        completed = subprocess.run([sys.executable, str(path)], cwd=ROOT, text=True, capture_output=True)
        if completed.returncode != 0:
            raise AcceptanceError(f"delegated validator failed: {path.name}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
        passed.append(path.name)
    return passed


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


def wait_http(url: str) -> None:
    end = time.monotonic() + 15
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
    for path in (shutil.which("chromedriver"), "/usr/bin/chromedriver", "/usr/local/share/chromedriver-linux64/chromedriver"):
        if path and Path(path).is_file():
            return str(path)
    raise AcceptanceError("chromedriver unavailable")


def wait_driver() -> None:
    end = time.monotonic() + 15
    while time.monotonic() < end:
        try:
            value = request("GET", "/status")
            if isinstance(value, dict) and value.get("ready"):
                return
        except Exception:
            pass
        time.sleep(.2)
    raise AcceptanceError("chromedriver not ready")


def session() -> str:
    value = request("POST", "/session", {"capabilities": {"alwaysMatch": {"browserName": "chrome", "goog:chromeOptions": {"args": ["--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-background-networking", "--disable-component-update", "--disable-extensions", "--disable-sync", "--no-first-run", "--window-size=1280,960"]}}}}, 60)
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


def navigate(sid: str, reference: str) -> None:
    request("POST", f"/session/{sid}/url", {"url": f"{SERVER}/{reference}"})
    end = time.monotonic() + 15
    while time.monotonic() < end:
        if execute(sid, "return document.readyState") == "complete":
            return
        time.sleep(.1)
    raise AcceptanceError(f"reference did not finish loading: {reference}")


def isolate_a11y(sid: str, case_id: str) -> None:
    media(sid, [])
    execute(sid, f"""
const root=document.documentElement;
for(const name of ['data-glz-motion','data-glz-transparency','data-glz-contrast','data-glz-boundaries','data-glz-text-scale','data-glz-touch-assistance','data-glz-material-clarity','data-glz-expression','data-glz-accent','data-mode']) root.removeAttribute(name);
root.style.fontSize=''; root.dir='ltr';
for(const scene of document.querySelectorAll('[data-a11y-case]')) scene.hidden=scene.dataset.a11yCase!=={json.dumps(case_id)};
return true;
""")


def isolate_responsive(sid: str, scene_id: str) -> None:
    execute(sid, f"""
document.documentElement.dir='ltr';
for(const scene of document.querySelectorAll('[data-adaptation-scene]')) scene.hidden=scene.dataset.adaptationScene!=={json.dumps(scene_id)};
const intro=document.querySelector('.intro');if(intro)intro.hidden=true;window.scrollTo(0,0);return true;
""")


def send_tab(sid: str) -> None:
    request("POST", f"/session/{sid}/actions", {"actions": [{"type": "key", "id": "keyboard", "actions": [{"type": "keyDown", "value": "\ue004"}, {"type": "keyUp", "value": "\ue004"}]}]})


def screenshot(sid: str, name: str) -> str:
    encoded = request("GET", f"/session/{sid}/screenshot")
    require(isinstance(encoded, str) and encoded, f"no screenshot bytes for {name}")
    ARTIFACTS.mkdir(exist_ok=True)
    path = ARTIFACTS / f"glaze-v1.2-accessibility-testing-{name}.png"
    path.write_bytes(base64.b64decode(encoded))
    require(path.stat().st_size > 5000, f"invalid screenshot {path}")
    return path.name


def target_rects(sid: str, selector: str) -> list[dict[str, Any]]:
    value = execute(sid, f"return [...document.querySelectorAll({json.dumps(selector)})].filter(e=>!e.hidden&&getComputedStyle(e).display!=='none'&&e.getClientRects().length).map(e=>{{const b=e.getBoundingClientRect();return{{id:e.id||e.textContent.trim(),w:b.width,h:b.height}}}});")
    require(isinstance(value, list), "could not read target geometry")
    return value


def target_floor(items: list[dict[str, Any]], minimum: int, label: str) -> None:
    bad = [item for item in items if float(item.get("w", 0)) < minimum or float(item.get("h", 0)) < minimum]
    require(not bad, f"{label} {minimum}px target floor drifted: {bad}")


def ax_role_names(sid: str) -> list[tuple[str, str]]:
    cdp(sid, "Accessibility.enable")
    tree = cdp(sid, "Accessibility.getFullAXTree")
    require(isinstance(tree, dict) and isinstance(tree.get("nodes"), list), "Chrome accessibility tree unavailable")
    result: list[tuple[str, str]] = []
    for node in tree["nodes"]:
        role = node.get("role", {}).get("value") if isinstance(node.get("role"), dict) else None
        name = node.get("name", {}).get("value") if isinstance(node.get("name"), dict) else None
        if isinstance(role, str) and isinstance(name, str):
            result.append((role, name))
    return result


def run_machine_observable(sid: str) -> dict[str, Any]:
    evidence: dict[str, Any] = {"screenshots": []}
    navigate(sid, A11Y_REFERENCE)
    viewport(sid, 900, 900)

    isolate_a11y(sid, "touch-compact")
    base_targets = target_rects(sid, "#touch-row button")
    target_floor(base_targets, 48, "default accessibility")
    roles = ax_role_names(sid)
    buttons = {name for role, name in roles if role.lower() == "button"}
    require({"Save", "Cancel", "More options"}.issubset(buttons), f"accessibility-tree button names drifted: {sorted(buttons)}")
    execute(sid, "document.body.tabIndex=-1;document.body.focus();return document.activeElement===document.body;")
    order: list[str] = []
    for _ in range(3):
        send_tab(sid)
        order.append(str(execute(sid, "return document.activeElement?.id||''")))
    require(order == ["touch-primary", "touch-secondary", "touch-more"], f"real Tab focus order drifted: {order}")
    execute(sid, "document.documentElement.dataset.glzTouchAssistance='true';return true;")
    assisted = target_rects(sid, "#touch-row button")
    target_floor(assisted, 56, "Touch Assistance")
    evidence["keyboardTabOrder"] = order
    evidence["accessibilityTreeButtons"] = sorted({name for name in buttons if name in {"Save", "Cancel", "More options"}})
    evidence["defaultTargets"] = base_targets
    evidence["assistedTargets"] = assisted
    evidence["screenshots"].append(screenshot(sid, "keyboard-touch"))

    isolate_a11y(sid, "contrast-boundaries")
    execute(sid, "document.documentElement.dataset.glzContrast='increased';document.documentElement.dataset.glzBoundaries='show';document.getElementById('contrast-focus').focus();return true;")
    focus = execute(sid, "const f=getComputedStyle(document.getElementById('contrast-focus'));const s=getComputedStyle(document.getElementById('contrast-surface'));return {outlineWidth:parseFloat(f.outlineWidth)||0,outlineStyle:f.outlineStyle,surfaceBorder:parseFloat(s.borderTopWidth)||0};")
    require(float(focus.get("outlineWidth", 0)) >= 4 and focus.get("outlineStyle") != "none", f"visible Increased Contrast focus drifted: {focus}")
    require(float(focus.get("surfaceBorder", 0)) >= 3, f"Show Boundaries surface distinction drifted: {focus}")
    evidence["visibleFocus"] = focus

    isolate_a11y(sid, "rt-clear")
    execute(sid, "document.documentElement.dataset.glzTransparency='reduced';document.documentElement.dataset.glzMaterialClarity='clear';return true;")
    readability = execute(sid, """const nodes=[document.querySelector('#rt-semantic strong'),document.querySelector('#rt-semantic p')];return nodes.map(e=>{const s=getComputedStyle(e),b=e.getBoundingClientRect();return {text:e.textContent.trim(),filter:s.filter,textShadow:s.textShadow,opacity:parseFloat(s.opacity),color:s.color,w:b.width,h:b.height}});""")
    require(isinstance(readability, list) and readability, "could not read material readability probes")
    for item in readability:
        require(item.get("filter") in ("none", "") and item.get("textShadow") == "none" and float(item.get("opacity", 0)) >= .99, f"material fallback altered text sharpness/visibility: {item}")
        require(float(item.get("w", 0)) > 0 and float(item.get("h", 0)) > 0 and item.get("color") not in ("transparent", "rgba(0, 0, 0, 0)"), f"material fallback hid readable text: {item}")
    evidence["materialReadability"] = readability

    isolate_a11y(sid, "fc-accent")
    vision_results: dict[str, Any] = {}
    for deficiency in ("achromatopsia", "deuteranopia", "protanopia", "tritanopia"):
        cdp(sid, "Emulation.setEmulatedVisionDeficiency", {"type": deficiency})
        state = execute(sid, """const b=document.getElementById('fc-selected'),s=document.getElementById('fc-protected'),bc=getComputedStyle(b),sc=getComputedStyle(s);return {pressed:b.getAttribute('aria-pressed'),selectedText:b.textContent.trim(),securityText:s.innerText.trim(),selectedBorder:parseFloat(bc.borderTopWidth)||0,semanticBorder:parseFloat(sc.borderInlineStartWidth)||0};""")
        require(state.get("pressed") == "true" and state.get("selectedText") == "Selected action", f"{deficiency} lost selected-state semantics: {state}")
        require("Security action required" in str(state.get("securityText", "")) and float(state.get("semanticBorder", 0)) > 0, f"{deficiency} lost protected semantic structure: {state}")
        require(float(state.get("selectedBorder", 0)) > 0, f"{deficiency} selected state became color-only: {state}")
        vision_results[deficiency] = state
    cdp(sid, "Emulation.setEmulatedVisionDeficiency", {"type": "none"})
    evidence["visionDeficiencySimulations"] = vision_results
    evidence["screenshots"].append(screenshot(sid, "color-vision-reset"))

    navigate(sid, RESPONSIVE_REFERENCE)
    viewport(sid, 320, 760)
    isolate_responsive(sid, "320-mobile")
    mobile = execute(sid, "const s=document.querySelector('[data-adaptation-scene=\"320-mobile\"]');const b=s.getBoundingClientRect();return {layout:s.dataset.glzLayoutClass,input:s.dataset.inputProfile,width:innerWidth,scrollWidth:document.documentElement.scrollWidth,left:b.left,right:b.right};")
    require(mobile.get("layout") == "compact" and mobile.get("input") == "touch", f"mobile accessibility composition drifted: {mobile}")
    require(int(mobile.get("scrollWidth", 9999)) <= 321 and float(mobile.get("left", -2)) >= -.5 and float(mobile.get("right", 9999)) <= 320.5, f"320px mobile containment drifted: {mobile}")
    mobile_targets = target_rects(sid, '[data-adaptation-scene="320-mobile"] button')
    target_floor(mobile_targets, 48, "320px mobile")
    evidence["mobile"] = {**mobile, "targets": mobile_targets}

    navigate(sid, RESPONSIVE_REFERENCE)
    viewport(sid, 1280, 900)
    isolate_responsive(sid, "tv-far-view")
    far = execute(sid, "const s=document.querySelector('[data-adaptation-scene=\"tv-far-view\"]');return {layout:s.dataset.glzLayoutClass,input:s.dataset.inputProfile,scrollWidth:document.documentElement.scrollWidth,width:innerWidth};")
    require(far.get("layout") == "large" and far.get("input") == "directional", f"far-view accessibility composition drifted: {far}")
    require(int(far.get("scrollWidth", 9999)) <= int(far.get("width", 0)) + 1, f"far-view page overflowed: {far}")
    far_targets = target_rects(sid, '[data-adaptation-scene="tv-far-view"] button')
    target_floor(far_targets, 56, "far-view")
    evidence["farView"] = {**far, "targets": far_targets}
    evidence["screenshots"].append(screenshot(sid, "far-view"))

    navigate(sid, RESPONSIVE_REFERENCE)
    viewport(sid, 1280, 960)
    isolate_responsive(sid, "rtl")
    execute(sid, "document.documentElement.dir='rtl';return true;")
    rtl = execute(sid, "const s=document.querySelector('[data-adaptation-scene=\"rtl\"]'),n=s.querySelector('nav'),c=n.querySelector('[aria-current=\"page\"]');return {direction:getComputedStyle(document.body).direction,navDirection:getComputedStyle(n).direction,current:c?.textContent.trim()||'',currentState:c?.getAttribute('aria-current')||'',width:innerWidth,scrollWidth:document.documentElement.scrollWidth};")
    require(rtl.get("direction") == "rtl" and rtl.get("navDirection") == "rtl", f"RTL direction did not propagate: {rtl}")
    require(rtl.get("current") == "Current" and rtl.get("currentState") == "page", f"RTL current-location semantics drifted: {rtl}")
    require(int(rtl.get("scrollWidth", 9999)) <= int(rtl.get("width", 0)) + 1, f"RTL reference overflowed: {rtl}")
    evidence["rtl"] = rtl
    evidence["screenshots"].append(screenshot(sid, "rtl"))
    return evidence


def main() -> int:
    http = driver = None
    sid: str | None = None
    evidence_path = ARTIFACTS / "glaze-v1.2-accessibility-testing-evidence.json"
    evidence: dict[str, Any] = {"sourceRevision": revision(), "status": "started"}
    ARTIFACTS.mkdir(exist_ok=True)
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    try:
        contract = validate_source()
        evidence["delegatedValidators"] = run_delegated()
        http = subprocess.Popen([sys.executable, "-m", "http.server", str(WEB_PORT), "--bind", HOST, "--directory", str(ROOT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wait_http(f"{SERVER}/{A11Y_REFERENCE}")
        driver = subprocess.Popen([chromedriver(), f"--port={DRIVER_PORT}", "--allowed-ips=127.0.0.1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wait_driver()
        sid = session()
        evidence["machineObservable"] = run_machine_observable(sid)
        evidence["status"] = "passed"
        evidence["boundedAutomatedAccessibilityTestingEstablished"] = contract.get("evidenceBoundary", {}).get("boundedAutomatedAccessibilityTestingEstablished")
        evidence["phase5AccessibilityTestingComplete"] = False
        evidence["notEstablished"] = contract.get("evidenceBoundary", {}).get("notEstablished", [])
        evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print("PASS: GLAZE UI V1.2 bounded automated Accessibility Testing; browser/keyboard/accessibility-tree evidence established, human and assistive-technology acceptance remains open.")
        return 0
    except Exception as error:
        evidence["status"] = "failed"
        evidence["error"] = str(error)
        evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print(f"GLAZE UI V1.2 Accessibility Testing failed: {error}", file=sys.stderr)
        return 1
    finally:
        if sid:
            try:
                request("DELETE", f"/session/{sid}", timeout=5)
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
    raise SystemExit(main())

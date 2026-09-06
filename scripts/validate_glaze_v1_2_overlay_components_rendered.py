#!/usr/bin/env python3
"""Rendered acceptance for the bounded GLAZE UI V1.2 Overlay component Candidate."""
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
WEB_PORT = 8795
DRIVER_PORT = 9545
SERVER = f"http://{HOST}:{WEB_PORT}"
DRIVER = f"http://{HOST}:{DRIVER_PORT}"
REFERENCE = "reference/v1.2/overlay-components.html"
CONTRACT = ROOT / "contracts/v1.2/overlay-components.candidate.json"
CSS = ROOT / "css/glaze-v1.2-overlay-components.candidate.css"
ENTRYPOINT = ROOT / "css/glaze-v1.2.0-candidate.css"
WORKFLOW = ROOT / ".github/workflows/glaze-v1.2-overlay-components.yml"
CATALOG = ROOT / "contracts/components/v1/catalog.json"
CHROME = ROOT / "contracts/v1.2/chrome-optics.candidate.json"
DEPTH = ROOT / "contracts/v1.2/depth.candidate.json"
CORE_TOKENS = ROOT / "contracts/v1.2/core-tokens.candidate.json"
EXPECTED_COMPONENTS = ["GlzTooltip", "GlzPopover", "GlzMenu", "GlzDialog", "GlzSheet", "GlzToast"]


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
    for path in (CONTRACT, CSS, ENTRYPOINT, WORKFLOW, ROOT / REFERENCE, CATALOG, CHROME, DEPTH, CORE_TOKENS, ROOT / "css/glaze-v1.overlay.css"):
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    contract = load(CONTRACT)
    catalog = load(CATALOG)
    chrome = load(CHROME)
    core = load(CORE_TOKENS)
    require(contract.get("version") == "1.2.0-candidate", "Overlay contract version drifted")
    require(contract.get("lifecycle") == "candidate" and contract.get("consumerEligible") is False, "Overlay Candidate boundary drifted")
    require(contract.get("stableBaseline") == "1.1.0", "Overlay Stable baseline drifted")
    require(contract.get("tier") == "overlay", "Overlay tier drifted")
    require(catalog.get("tiers", {}).get("overlay") == EXPECTED_COMPONENTS, "Stable Overlay catalog drifted")
    require([item.get("id") for item in contract.get("components", [])] == EXPECTED_COMPONENTS, "V1.2 Overlay family set/order drifted")
    rules = contract.get("universalRules", {})
    expected_true = (
        "clarityBeforeMaterial", "nestedBackdropBlurProhibited", "consequentialDecisionSurfacesRemainNonBackdropDependent",
        "semanticMeaningCannotDependOnlyOnAtmosphericColor", "focusRestorationRequired", "escapeDismissalWhereApplicable",
        "keyboardRequired", "reducedMotionRequired", "reducedTransparencyRequired", "increasedContrastRequired",
        "forcedColorsPlatformAuthoritative", "textScale200Required", "rtlWhereApplicable", "responsiveTransformationRequired",
        "noNewRuntimeDependency",
    )
    require(all(rules.get(key) is True for key in expected_true), "Overlay universal rule drifted")
    require(rules.get("minimumTargetPx") == 48 and rules.get("assistedTargetPx") == 56, "Overlay target floor drifted")
    require(core.get("families", {}).get("state", {}).get("consumerClaimBlocked") is True, "Overlay tranche incorrectly assumes complete state-token authority")
    boundary = contract.get("stateTokenBoundary", {})
    require(boundary.get("completeV12StateTokenOwnerEstablished") is False and boundary.get("componentLocalStateRefinementOnly") is True, "Overlay state-token boundary drifted")
    require(boundary.get("mayImportTokensStatesJsonAsV12Authority") is False, "Overlay tranche permits unrelated state-token authority")
    feedback = contract.get("feedbackBoundary", {})
    require(feedback.get("routineToastRole") == "status" and feedback.get("routineToastLive") == "polite", "routine toast semantics drifted")
    require(feedback.get("criticalFailureRequiresPersistentNonToastPresentation") is True, "critical failure toast-only prohibition drifted")
    materials = contract.get("materialAuthority", {})
    require(materials.get("chromeOptics") == "contracts/v1.2/chrome-optics.candidate.json", "Overlay chrome authority drifted")
    require(materials.get("depth") == "contracts/v1.2/depth.candidate.json", "Overlay depth authority drifted")
    require(materials.get("newNumericMaterialCalibrationIntroduced") is False, "Overlay tranche introduced competing material calibration")
    expected_frost = {"GlzTooltip": "clear", "GlzPopover": "frost", "GlzMenu": "frost", "GlzSheet": "dense-frost", "GlzToast": "frost"}
    for name, frost in expected_frost.items():
        require(chrome.get("components", {}).get(name, {}).get("frost") == frost, f"chrome material authority drifted for {name}")
    require(chrome.get("rules", {}).get("consequentialDecisionSurfacesRemainNonBackdropDependent") is True, "chrome decision-surface rule drifted")

    css = CSS.read_text(encoding="utf-8")
    for marker in (
        '.glz1-tooltip', '.glz1-popover', '.glz1-menu', '.glz1-dialog', '.glz1-sheet', '.glz1-toast',
        'consequential modal decisions', 'backdrop-filter: none !important', '.glz12-persistent-failure',
        '.glz1-toast-region > .glz1-toast:nth-of-type(n+4)', 'data-mode="increased-contrast"',
        '@media (prefers-reduced-motion: reduce)', '@media (forced-colors: active)',
    ):
        require(marker.lower() in css.lower(), f"Overlay CSS marker missing: {marker}")

    reference = (ROOT / REFERENCE).read_text(encoding="utf-8")
    for marker in (
        'role="tooltip"', 'aria-haspopup="dialog"', 'role="menu"', 'role="menuitemcheckbox"', 'role="menuitemradio"',
        '<dialog id="dialog-sample"', 'aria-modal="true"', 'role="status" aria-live="polite"',
        'id="persistent-failure"', 'role="alert"', 'window.__glazeOverlay',
    ):
        require(marker in reference, f"Overlay reference semantic marker missing: {marker}")
    require('document.addEventListener(\'keydown\'' in reference and "event.key !== 'Escape'" in reference, "Overlay reference Escape handling missing")
    require("critical-trigger" in reference and "persistent-failure" in reference and "toast-critical" in reference, "critical feedback reference incomplete")

    impl = contract.get("implementation", {})
    require(impl.get("webLayer") == "css/glaze-v1.2-overlay-components.candidate.css", "Overlay CSS binding drifted")
    require(impl.get("reference") == REFERENCE, "Overlay reference binding drifted")
    require(impl.get("renderedValidator") == "scripts/validate_glaze_v1_2_overlay_components_rendered.py", "Overlay validator binding drifted")
    require(impl.get("workflow") == ".github/workflows/glaze-v1.2-overlay-components.yml", "Overlay workflow binding drifted")

    entry = ENTRYPOINT.read_text(encoding="utf-8")
    chain = [
        '@import url("./glaze-v1.2-structure-components.candidate.css")',
        '@import url("./glaze-v1.2-overlay-components.candidate.css")',
        '@import url("./glaze-v1.2-accessibility.candidate.css")',
    ]
    require(all(item in entry for item in chain), "Candidate entrypoint missing Overlay import chain")
    require([entry.index(item) for item in chain] == sorted(entry.index(item) for item in chain), "Overlay/accessibility import order drifted")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    require("validate_glaze_v1_2_overlay_components_rendered.py" in workflow, "Overlay workflow does not invoke rendered validator")
    require("github.event.pull_request.head.sha || github.sha" in workflow, "Overlay workflow is not exact-head pinned")


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
    raise AcceptanceError("Overlay reference did not finish loading")


def screenshot(sid: str, name: str) -> None:
    encoded = request("GET", f"/session/{sid}/screenshot")
    require(isinstance(encoded, str) and encoded, "no screenshot bytes")
    ARTIFACTS.mkdir(exist_ok=True)
    path = ARTIFACTS / f"glaze-v1.2-overlay-components-{name}.png"
    path.write_bytes(base64.b64decode(encoded))
    require(path.stat().st_size > 7000, f"invalid screenshot {path}")


def press_key(sid: str, key: str) -> None:
    request("POST", f"/session/{sid}/actions", {"actions": [{"type": "key", "id": "keyboard", "actions": [
        {"type": "keyDown", "value": key}, {"type": "keyUp", "value": key}
    ]}]})
    request("DELETE", f"/session/{sid}/actions")


def reset_scene(sid: str) -> None:
    execute(sid, """
      document.documentElement.dir='ltr';
      document.documentElement.dataset.glzAppearance='light';
      document.documentElement.dataset.mode='';
      document.documentElement.dataset.glzTransparency='full';
      document.documentElement.dataset.glzTextScale='100';
      document.documentElement.dataset.glzTouchAssistance='false';
      document.documentElement.dataset.glzMaterialPerformance='full';
      if (window.__glazeOverlay) {
        window.__glazeOverlay.closePopover(false); window.__glazeOverlay.closeMenu(false); window.__glazeOverlay.closeSheet();
        for (const id of ['toast-routine','toast-critical','toast-third','toast-fourth']) window.__glazeOverlay.hideToast(id);
      }
      document.getElementById('persistent-failure').hidden=true;
      return true;
    """)
    media(sid, [])
    time.sleep(.1)


def target_floor(sid: str, selector: str, minimum: float) -> None:
    result = execute(sid, f"""
      const nodes=[...document.querySelectorAll({json.dumps(selector)})].filter(el=>{{const s=getComputedStyle(el);return s.display!=='none'&&s.visibility!=='hidden'&&el.getClientRects().length;}});
      return nodes.map(el=>{{const r=el.getBoundingClientRect();return {{id:el.id,w:r.width,h:r.height}};}});
    """)
    require(isinstance(result, list) and result, f"no visible targets for {selector}")
    bad = [item for item in result if item["w"] + .1 < minimum or item["h"] + .1 < minimum]
    require(not bad, f"target floor {minimum}px failed for {bad}")


def appearance_acceptance(sid: str) -> None:
    for appearance in ("light", "dark", "deep-dark"):
        reset_scene(sid)
        execute(sid, f"document.documentElement.dataset.glzAppearance={json.dumps(appearance)}; document.getElementById('popover-trigger').click(); return true;")
        time.sleep(.22)
        state = execute(sid, """
          const p=document.getElementById('popover-sample'), s=getComputedStyle(p), b=getComputedStyle(document.body);
          return {appearance:document.documentElement.dataset.glzAppearance, open:p.dataset.open, opacity:parseFloat(s.opacity), bg:b.backgroundColor, fg:b.color, overflow:document.documentElement.scrollWidth-innerWidth};
        """)
        require(state["appearance"] == appearance and state["open"] == "true" and state["opacity"] > .9, f"{appearance} popover did not render: {state}")
        require(state["bg"] != "rgba(0, 0, 0, 0)" and state["fg"] != "rgba(0, 0, 0, 0)", f"{appearance} appearance lost readable colors: {state}")
        require(state["overflow"] <= 1, f"{appearance} reference overflows viewport: {state}")
        screenshot(sid, appearance)


def tooltip_acceptance(sid: str) -> None:
    reset_scene(sid)
    execute(sid, "document.getElementById('tooltip-trigger').focus(); return true;")
    time.sleep(.2)
    state = execute(sid, """
      const t=document.getElementById('tooltip-sample'), s=getComputedStyle(t), trigger=document.getElementById('tooltip-trigger');
      return {open:t.dataset.open, hidden:t.getAttribute('aria-hidden'), role:t.getAttribute('role'), pointer:s.pointerEvents, interactive:t.querySelectorAll('button,a,input,select,textarea,[tabindex]:not([tabindex="-1"])').length, described:trigger.getAttribute('aria-describedby')};
    """)
    require(state["open"] == "true" and state["hidden"] == "false" and state["role"] == "tooltip", f"Tooltip focus behavior failed: {state}")
    require(state["pointer"] == "none" and state["interactive"] == 0, f"Tooltip became interactive: {state}")
    require("tooltip-help" in state["described"] and "tooltip-sample" in state["described"], "Tooltip is not supplementary to visible help")


def popover_acceptance(sid: str) -> None:
    reset_scene(sid)
    execute(sid, "document.getElementById('popover-trigger').click(); return true;")
    time.sleep(.22)
    state = execute(sid, """
      const p=document.getElementById('popover-sample'), t=document.getElementById('popover-trigger'), pr=p.getBoundingClientRect(), tr=t.getBoundingClientRect(), s=getComputedStyle(p);
      return {open:p.dataset.open, expanded:t.getAttribute('aria-expanded'), active:document.activeElement.id, gap:Math.abs(pr.top-tr.bottom), blur:s.backdropFilter||s.webkitBackdropFilter||'none'};
    """)
    require(state["open"] == "true" and state["expanded"] == "true" and state["active"] == "popover-input", f"Popover opening/focus failed: {state}")
    require(state["gap"] <= 24, f"Popover lost visible source relation: {state}")
    require(state["blur"] != "none", f"Full-profile Popover lost governed Frost: {state}")
    press_key(sid, "\ue00c")
    time.sleep(.12)
    closed = execute(sid, "return {open:document.getElementById('popover-sample').dataset.open,active:document.activeElement.id,expanded:document.getElementById('popover-trigger').getAttribute('aria-expanded')}")
    require(closed == {"open": "false", "active": "popover-trigger", "expanded": "false"}, f"Popover Escape/focus restoration failed: {closed}")


def menu_acceptance(sid: str) -> None:
    reset_scene(sid)
    execute(sid, "document.getElementById('menu-trigger').click(); return true;")
    time.sleep(.2)
    initial = execute(sid, "return {open:document.getElementById('menu-sample').dataset.open,active:document.activeElement.id,role:document.getElementById('menu-sample').getAttribute('role')}")
    require(initial == {"open": "true", "active": "menu-open", "role": "menu"}, f"Menu initial roving focus failed: {initial}")
    target_floor(sid, ".glz1-menu-item:not([aria-disabled=\"true\"])", 48)
    press_key(sid, "\ue015")
    require(execute(sid, "return document.activeElement.id") == "menu-pin", "ArrowDown did not move Menu focus")
    press_key(sid, "\ue00d")
    checked = execute(sid, "return {checked:document.getElementById('menu-pin').getAttribute('aria-checked'),mark:document.querySelector('#menu-pin .glz12-menu-mark').textContent}")
    require(checked["checked"] == "true" and checked["mark"] == "✓", f"Menu checkbox state failed: {checked}")
    press_key(sid, "\ue015")
    press_key(sid, "\ue015")
    require(execute(sid, "return document.activeElement.id") == "menu-comfortable", "Menu radio focus traversal failed")
    press_key(sid, "\ue00d")
    radios = execute(sid, "return {compact:document.getElementById('menu-compact').getAttribute('aria-checked'),comfortable:document.getElementById('menu-comfortable').getAttribute('aria-checked')}")
    require(radios == {"compact": "false", "comfortable": "true"}, f"Menu radio-group state failed: {radios}")
    press_key(sid, "\ue010")
    require(execute(sid, "return document.activeElement.id") == "menu-delete", "End did not skip disabled item and reach destructive Menu action")
    press_key(sid, "\ue00c")
    time.sleep(.1)
    closed = execute(sid, "return {open:document.getElementById('menu-sample').dataset.open,active:document.activeElement.id}")
    require(closed == {"open": "false", "active": "menu-trigger"}, f"Menu Escape/focus restoration failed: {closed}")


def dialog_acceptance(sid: str) -> None:
    reset_scene(sid)
    execute(sid, "document.getElementById('dialog-trigger').click(); return true;")
    time.sleep(.15)
    state = execute(sid, """
      const d=document.getElementById('dialog-sample'),s=getComputedStyle(d),r=d.getBoundingClientRect();
      return {open:d.open,active:document.activeElement.id,blur:s.backdropFilter||s.webkitBackdropFilter||'none',bg:s.backgroundColor,w:r.width,h:r.height};
    """)
    require(state["open"] is True and state["active"] == "dialog-cancel", f"Dialog initial modal/focus behavior failed: {state}")
    require(state["blur"] == "none", f"Consequential Dialog depends on backdrop blur: {state}")
    require(state["bg"] != "rgba(0, 0, 0, 0)", f"Consequential Dialog lost opaque/near-opaque decision plane: {state}")
    target_floor(sid, "#dialog-sample .glz1-overlay-button", 48)
    press_key(sid, "\ue00c")
    time.sleep(.15)
    closed = execute(sid, "return {open:document.getElementById('dialog-sample').open,active:document.activeElement.id}")
    require(closed == {"open": False, "active": "dialog-trigger"}, f"Dialog Escape/focus restoration failed: {closed}")


def sheet_acceptance(sid: str) -> None:
    reset_scene(sid)
    viewport(sid, 1280, 900)
    execute(sid, "document.getElementById('sheet-trigger').click(); return true;")
    time.sleep(.3)
    wide = execute(sid, """
      const layer=document.getElementById('sheet-layer'),s=document.getElementById('sheet-sample'),r=s.getBoundingClientRect(),style=getComputedStyle(s),reading=getComputedStyle(document.querySelector('.glz12-sheet-reading-plane'));
      return {open:layer.dataset.open,active:document.activeElement.id,left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,iw:innerWidth,blur:style.backdropFilter||style.webkitBackdropFilter||'none',readingBlur:reading.backdropFilter||reading.webkitBackdropFilter||'none'};
    """)
    require(wide["open"] == "true" and wide["active"] == "sheet-close", f"wide Sheet opening/focus failed: {wide}")
    require(wide["right"] > wide["iw"] - 40 and wide["top"] < 40, f"wide Sheet did not become side sheet: {wide}")
    require(wide["blur"] != "none" and wide["readingBlur"] == "none", f"Sheet material/readability ownership failed: {wide}")
    press_key(sid, "\ue00c")
    time.sleep(.12)
    require(execute(sid, "return document.activeElement.id") == "sheet-trigger", "Sheet Escape did not restore focus")

    execute(sid, "document.documentElement.dir='rtl'; document.getElementById('sheet-trigger').click(); return true;")
    time.sleep(.3)
    rtl = execute(sid, "const r=document.getElementById('sheet-sample').getBoundingClientRect();return {left:r.left,right:r.right,iw:innerWidth}")
    require(rtl["left"] < 40 and rtl["right"] < rtl["iw"] - 40, f"RTL wide Sheet did not move to logical start: {rtl}")
    execute(sid, "window.__glazeOverlay.closeSheet(); document.documentElement.dir='ltr'; return true;")

    viewport(sid, 390, 760)
    execute(sid, "document.getElementById('sheet-trigger').click(); return true;")
    time.sleep(.3)
    compact = execute(sid, """
      const s=document.getElementById('sheet-sample'),r=s.getBoundingClientRect(),h=getComputedStyle(document.querySelector('.glz1-sheet-handle'));
      return {left:r.left,right:r.right,bottom:r.bottom,width:r.width,iw:innerWidth,ih:innerHeight,handle:h.display,scrollWidth:document.documentElement.scrollWidth};
    """)
    require(compact["bottom"] > compact["ih"] - 30 and compact["width"] > 340 and compact["handle"] != "none", f"compact Sheet did not become bottom sheet: {compact}")
    require(compact["scrollWidth"] <= compact["iw"] + 1, f"compact Sheet caused page overflow: {compact}")
    target_floor(sid, "#sheet-sample .glz1-overlay-button", 48)
    execute(sid, "window.__glazeOverlay.closeSheet(); return true;")
    viewport(sid, 1280, 1200)


def toast_acceptance(sid: str) -> None:
    reset_scene(sid)
    execute(sid, "document.getElementById('toast-trigger').click(); return true;")
    time.sleep(.22)
    routine = execute(sid, """
      const t=document.getElementById('toast-routine'); return {open:t.dataset.open,role:t.getAttribute('role'),live:t.getAttribute('aria-live'),hidden:t.getAttribute('aria-hidden')};
    """)
    require(routine == {"open": "true", "role": "status", "live": "polite", "hidden": "false"}, f"routine Toast semantics failed: {routine}")
    target_floor(sid, "#toast-routine button", 48)
    execute(sid, "document.getElementById('toast-undo').click(); return true;")
    require(execute(sid, "return document.getElementById('toast-routine').dataset.open") == "false", "Toast Undo did not dismiss transient status")

    execute(sid, "for(const id of ['toast-routine','toast-critical','toast-third','toast-fourth']){const t=document.getElementById(id);t.dataset.open='true';t.setAttribute('aria-hidden','false');} return true;")
    time.sleep(.22)
    stack = execute(sid, "return ['toast-routine','toast-critical','toast-third','toast-fourth'].map(id=>({id,display:getComputedStyle(document.getElementById(id)).display}))")
    require(all(item["display"] != "none" for item in stack[:3]) and stack[3]["display"] == "none", f"Toast stack is not bounded to three: {stack}")

    reset_scene(sid)
    execute(sid, "document.getElementById('critical-trigger').click(); return true;")
    time.sleep(.22)
    critical = execute(sid, """
      const p=document.getElementById('persistent-failure'),t=document.getElementById('toast-critical');
      return {persistentHidden:p.hidden,persistentRole:p.getAttribute('role'),toastOpen:t.dataset.open,toastRole:t.getAttribute('role'),toastCopy:t.textContent};
    """)
    require(critical["persistentHidden"] is False and critical["persistentRole"] == "alert", f"critical failure lacks persistent presentation: {critical}")
    require(critical["toastOpen"] == "true" and critical["toastRole"] == "status" and "Persistent details" in critical["toastCopy"], f"critical Toast is not clearly supplementary: {critical}")


def accessibility_acceptance(sid: str) -> None:
    reset_scene(sid)
    execute(sid, "document.documentElement.dataset.glzTransparency='reduced'; document.getElementById('popover-trigger').click(); document.getElementById('sheet-trigger').click(); return true;")
    time.sleep(.25)
    reduced = execute(sid, """
      const p=getComputedStyle(document.getElementById('popover-sample')),s=getComputedStyle(document.getElementById('sheet-sample'));
      return {popover:p.backdropFilter||p.webkitBackdropFilter||'none',sheet:s.backdropFilter||s.webkitBackdropFilter||'none'};
    """)
    require(reduced == {"popover": "none", "sheet": "none"}, f"Reduced Transparency did not remove Overlay blur: {reduced}")

    reset_scene(sid)
    execute(sid, "document.documentElement.dataset.mode='reduced-motion'; document.getElementById('menu-trigger').click(); return true;")
    time.sleep(.1)
    motion = execute(sid, "return getComputedStyle(document.getElementById('menu-sample')).transitionDuration")
    require(set(part.strip() for part in motion.split(',')) <= {"0s"}, f"Reduced Motion retained Menu transition: {motion}")

    reset_scene(sid)
    execute(sid, "document.documentElement.dataset.mode='increased-contrast'; document.getElementById('popover-trigger').click(); return true;")
    time.sleep(.1)
    border = execute(sid, "return parseFloat(getComputedStyle(document.getElementById('popover-sample')).borderTopWidth)")
    require(border >= 2, f"Increased Contrast did not strengthen Overlay boundary: {border}")

    reset_scene(sid)
    media(sid, [{"name": "forced-colors", "value": "active"}])
    execute(sid, "document.getElementById('menu-trigger').click(); return true;")
    time.sleep(.1)
    forced = execute(sid, """
      const s=getComputedStyle(document.getElementById('menu-sample')); return {blur:s.backdropFilter||s.webkitBackdropFilter||'none',shadow:s.boxShadow,transition:s.transitionDuration};
    """)
    require(forced["blur"] == "none" and forced["shadow"] == "none", f"Forced Colors did not take platform authority over Overlay effects: {forced}")
    media(sid, [])

    reset_scene(sid)
    execute(sid, "document.documentElement.dataset.glzTouchAssistance='true'; document.getElementById('menu-trigger').click(); return true;")
    time.sleep(.1)
    target_floor(sid, ".glz1-menu-item:not([aria-disabled=\"true\"])", 56)

    reset_scene(sid)
    viewport(sid, 390, 760)
    execute(sid, "document.documentElement.dataset.glzTextScale='200'; document.getElementById('sheet-trigger').click(); return true;")
    time.sleep(.25)
    large = execute(sid, "return {sw:document.documentElement.scrollWidth,iw:innerWidth,sheet:document.getElementById('sheet-sample').getBoundingClientRect().width}")
    require(large["sw"] <= large["iw"] + 1 and large["sheet"] <= large["iw"] - 8, f"200% compact Overlay reflow failed: {large}")
    screenshot(sid, "compact-200")
    viewport(sid, 1280, 1200)


def run_rendered() -> None:
    web = subprocess.Popen([sys.executable, "-m", "http.server", str(WEB_PORT), "--bind", HOST], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    driver = subprocess.Popen([chromedriver(), f"--port={DRIVER_PORT}"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sid: str | None = None
    try:
        wait_http(f"{SERVER}/{REFERENCE}")
        wait_driver()
        sid = session()
        viewport(sid, 1280, 1200)
        navigate(sid)
        screenshot(sid, "baseline")
        appearance_acceptance(sid)
        tooltip_acceptance(sid)
        popover_acceptance(sid)
        menu_acceptance(sid)
        dialog_acceptance(sid)
        sheet_acceptance(sid)
        toast_acceptance(sid)
        accessibility_acceptance(sid)
    finally:
        if sid:
            try:
                request("DELETE", f"/session/{sid}")
            except Exception:
                pass
        for process in (driver, web):
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


def main() -> int:
    try:
        validate_source()
        run_rendered()
    except AcceptanceError as error:
        print(f"GLAZE UI V1.2 Overlay component acceptance failed: {error}", file=sys.stderr)
        return 1
    print("GLAZE UI V1.2 bounded Overlay component Candidate acceptance passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Rendered acceptance for the bounded GLAZE UI V1.2 Structure component Candidate."""
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
WEB_PORT = 8794
DRIVER_PORT = 9544
SERVER = f"http://{HOST}:{WEB_PORT}"
DRIVER = f"http://{HOST}:{DRIVER_PORT}"
REFERENCE = "reference/v1.2/structure-components.html"
CONTRACT = ROOT / "contracts/v1.2/structure-components.candidate.json"
CSS = ROOT / "css/glaze-v1.2-structure-components.candidate.css"
ENTRYPOINT = ROOT / "css/glaze-v1.2.0-candidate.css"
WORKFLOW = ROOT / ".github/workflows/glaze-v1.2-structure-components.yml"
CATALOG = ROOT / "contracts/components/v1/catalog.json"
CORE_TOKENS = ROOT / "contracts/v1.2/core-tokens.candidate.json"

EXPECTED_COMPONENTS = [
    "GlzCard", "GlzList", "GlzTable", "GlzTabs",
    "GlzSidebar", "GlzNavigationRail", "GlzDock", "GlzToolbar",
]
TARGET_IDS = [
    "card-interactive", "list-overview", "list-activity", "list-archive", "table-sort",
    "tab-overview", "tab-events", "tab-access",
    "sidebar-home", "sidebar-files", "sidebar-settings", "rail-home", "rail-files",
    "dock-home", "dock-search", "dock-files",
    "toolbar-primary", "toolbar-secondary", "toolbar-tertiary", "toolbar-overflow",
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
    for path in (CONTRACT, CSS, ENTRYPOINT, WORKFLOW, ROOT / REFERENCE, CATALOG, CORE_TOKENS):
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    contract = load(CONTRACT)
    catalog = load(CATALOG)
    core = load(CORE_TOKENS)
    require(contract.get("version") == "1.2.0-candidate", "structure contract version drifted")
    require(contract.get("lifecycle") == "candidate" and contract.get("consumerEligible") is False, "structure Candidate boundary drifted")
    require(contract.get("stableBaseline") == "1.1.0", "structure Stable baseline drifted")
    require(contract.get("tier") == "structure", "structure tier drifted")
    require(catalog.get("tiers", {}).get("structure") == EXPECTED_COMPONENTS, "Stable structure catalog drifted")
    require([item.get("id") for item in contract.get("components", [])] == EXPECTED_COMPONENTS, "V1.2 Structure family set/order drifted")
    rules = contract.get("universalRules", {})
    expected_true = (
        "clarityBeforeMaterial", "durableReadingAndDenseDataPreferOpaqueOrNearOpaque", "nestedBackdropBlurProhibited",
        "semanticMeaningCannotDependOnlyOnAtmosphericColor", "focusDistinctFromCurrentOrSelectedState", "keyboardRequired",
        "reducedMotionRequired", "reducedTransparencyRequired", "increasedContrastRequired", "forcedColorsPlatformAuthoritative",
        "textScale200Required", "rtlWhereApplicable", "responsiveTransformationRequired", "noNewRuntimeDependency",
    )
    require(all(rules.get(key) is True for key in expected_true), "structure universal rule drifted")
    require(rules.get("minimumTargetPx") == 48 and rules.get("assistedTargetPx") == 56, "structure target floor drifted")
    require(core.get("families", {}).get("state", {}).get("consumerClaimBlocked") is True, "Structure tranche incorrectly assumes complete state-token authority")
    boundary = contract.get("stateTokenBoundary", {})
    require(boundary.get("completeV12StateTokenOwnerEstablished") is False and boundary.get("componentLocalStateRefinementOnly") is True, "Structure state-token boundary drifted")
    require(boundary.get("mayImportTokensStatesJsonAsV12Authority") is False, "Structure tranche permits unrelated state-token authority")
    table = next(item for item in contract["components"] if item["id"] == "GlzTable")
    require(table.get("denseDataBackdropBlurProhibited") is True, "dense Table blur prohibition missing")
    toolbar = next(item for item in contract["components"] if item["id"] == "GlzToolbar")
    require(toolbar.get("priorityOneMustRemainReachable") is True, "Toolbar priority-one reachability rule missing")

    css = CSS.read_text(encoding="utf-8")
    require("blur(" not in css.lower(), "Structure refinement layer must not introduce new blur")
    for marker in (
        '.glz1-table tbody tr[data-selected="true"] > :first-child',
        '.glz1-tab[aria-selected="true"]::after',
        '.glz1-sidebar-item[aria-current="page"]',
        '.glz1-rail-item[aria-current="page"]',
        '.glz1-dock-item[aria-current="page"]',
        '[data-priority="1"]', 'data-mode="increased-contrast"',
        '@media (prefers-reduced-motion: reduce)', '@media (forced-colors: active)',
    ):
        require(marker in css, f"Structure CSS marker missing: {marker}")

    reference = (ROOT / REFERENCE).read_text(encoding="utf-8")
    for marker in (
        'id="card-interactive"', 'role="listbox"', 'aria-sort="none"', 'role="tablist"',
        'aria-current="page"', 'id="dock-sample"', 'role="toolbar"', 'data-priority="1"',
    ):
        require(marker in reference, f"Structure reference semantic marker missing: {marker}")

    impl = contract.get("implementation", {})
    require(impl.get("webLayer") == "css/glaze-v1.2-structure-components.candidate.css", "Structure CSS binding drifted")
    require(impl.get("reference") == REFERENCE, "Structure reference binding drifted")
    require(impl.get("renderedValidator") == "scripts/validate_glaze_v1_2_structure_components_rendered.py", "Structure validator binding drifted")
    require(impl.get("workflow") == ".github/workflows/glaze-v1.2-structure-components.yml", "Structure workflow binding drifted")

    entry = ENTRYPOINT.read_text(encoding="utf-8")
    chain = [
        '@import url("./glaze-v1.2-foundation-components.candidate.css")',
        '@import url("./glaze-v1.2-structure-components.candidate.css")',
        '@import url("./glaze-v1.2-accessibility.candidate.css")',
    ]
    require(all(item in entry for item in chain), "Candidate entrypoint missing Structure import chain")
    require([entry.index(item) for item in chain] == sorted(entry.index(item) for item in chain), "Structure/accessibility import order drifted")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    require("validate_glaze_v1_2_structure_components_rendered.py" in workflow, "Structure workflow does not invoke rendered validator")
    require("github.event.pull_request.head.sha || github.sha" in workflow, "Structure workflow is not exact-head pinned")


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
    raise AcceptanceError("Structure reference did not finish loading")


def screenshot(sid: str, name: str) -> None:
    encoded = request("GET", f"/session/{sid}/screenshot")
    require(isinstance(encoded, str) and encoded, "no screenshot bytes")
    ARTIFACTS.mkdir(exist_ok=True)
    path = ARTIFACTS / f"glaze-v1.2-structure-components-{name}.png"
    path.write_bytes(base64.b64decode(encoded))
    require(path.stat().st_size > 7000, f"invalid screenshot {path}")


def press_key(sid: str, key: str) -> None:
    request("POST", f"/session/{sid}/actions", {"actions": [{"type": "key", "id": "keyboard", "actions": [
        {"type": "keyDown", "value": key}, {"type": "keyUp", "value": key}
    ]}]})
    request("DELETE", f"/session/{sid}/actions")


STATE_JS = r"""
const ids = %s;
const targets = {};
for (const id of ids) {
  const el = document.getElementById(id);
  if (!el) { targets[id] = null; continue; }
  const style = getComputedStyle(el);
  const r = el.getBoundingClientRect();
  targets[id] = {w:r.width,h:r.height,display:style.display,visibility:style.visibility};
}
const card = document.getElementById('card-interactive');
const cardStyle = getComputedStyle(card);
const cardMarker = getComputedStyle(card.querySelector('.glz1-card-selection'));
const selectedList = document.querySelector('.glz12-list-option[aria-selected="true"]');
const listStyle = getComputedStyle(selectedList);
const listCheck = getComputedStyle(selectedList.querySelector('.glz1-list-check'));
const tableWrap = document.getElementById('table-wrap');
const tableWrapStyle = getComputedStyle(tableWrap);
const table = document.getElementById('table-sample');
const tableStyle = getComputedStyle(table);
const selectedCell = document.querySelector('#table-row-selected > :first-child');
const selectedCellStyle = getComputedStyle(selectedCell);
const selectedTab = document.querySelector('.glz1-tab[aria-selected="true"]');
const tabIndicator = getComputedStyle(selectedTab,'::after');
const sidebarCurrent = document.querySelector('.glz1-sidebar-item[aria-current="page"]');
const sidebarStyle = getComputedStyle(sidebarCurrent);
const rail = document.getElementById('rail-sample');
const railCurrent = document.querySelector('.glz1-rail-item[aria-current="page"]');
const railCurrentStyle = getComputedStyle(railCurrent);
const dock = document.getElementById('dock-sample');
const dockStyle = getComputedStyle(dock);
const dockCurrent = document.querySelector('.glz1-dock-item[aria-current="page"]');
const dockCurrentStyle = getComputedStyle(dockCurrent);
const listBackdrop = getComputedStyle(document.getElementById('list-sample'));
const sidebarBackdrop = getComputedStyle(document.getElementById('sidebar-sample'));
const toolbar = document.getElementById('toolbar-sample');
const toolbarStyle = getComputedStyle(toolbar);
const toolbarPrimary = getComputedStyle(document.getElementById('toolbar-primary'));
const toolbarSecondary = getComputedStyle(document.getElementById('toolbar-secondary'));
const toolbarTertiary = getComputedStyle(document.getElementById('toolbar-tertiary'));
const toolbarOverflow = getComputedStyle(document.getElementById('toolbar-overflow'));
return {
  ready: document.readyState,
  width: innerWidth,
  scrollWidth: document.documentElement.scrollWidth,
  dir: document.documentElement.dir || 'ltr',
  targets,
  card: {
    selected:card.dataset.selected, pressed:card.getAttribute('aria-pressed'), markerOpacity:parseFloat(cardMarker.opacity),
    borderInlineStart:parseFloat(cardStyle.borderInlineStartWidth), backdrop:cardStyle.backdropFilter || cardStyle.webkitBackdropFilter || 'none',
    transition:cardStyle.transitionDuration
  },
  list: {
    selectedId:selectedList && selectedList.id, markerOpacity:parseFloat(listCheck.opacity), borderInlineStart:parseFloat(listStyle.borderInlineStartWidth),
    borderLeft:parseFloat(listStyle.borderLeftWidth), borderRight:parseFloat(listStyle.borderRightWidth),
    backdrop:listBackdrop.backdropFilter || listBackdrop.webkitBackdropFilter || 'none'
  },
  table: {
    sort:document.getElementById('name-header').getAttribute('aria-sort'), rowMarkerWidth:document.querySelector('.glz12-table-row-marker').getBoundingClientRect().width,
    selectedBorder:parseFloat(selectedCellStyle.borderInlineStartWidth), wrapOverflowX:tableWrapStyle.overflowX,
    wrapClientWidth:tableWrap.clientWidth, tableScrollWidth:table.scrollWidth, backdrop:tableStyle.backdropFilter || tableStyle.webkitBackdropFilter || 'none'
  },
  tabs: {selectedId:selectedTab && selectedTab.id, indicatorHeight:parseFloat(tabIndicator.height)},
  navigation: {
    sidebarCurrent:sidebarCurrent && sidebarCurrent.id, sidebarBorderInlineStart:parseFloat(sidebarStyle.borderInlineStartWidth),
    sidebarLeft:parseFloat(sidebarStyle.borderLeftWidth), sidebarRight:parseFloat(sidebarStyle.borderRightWidth),
    railCurrent:railCurrent && railCurrent.id, railDisplay:getComputedStyle(rail).display,
    railShadow:railCurrentStyle.boxShadow, railOutline:parseFloat(railCurrentStyle.outlineWidth),
    dockCurrent:dockCurrent && dockCurrent.id, dockShadow:dockCurrentStyle.boxShadow, dockOutline:parseFloat(dockCurrentStyle.outlineWidth),
    dockBackdrop:dockStyle.backdropFilter || dockStyle.webkitBackdropFilter || 'none',
    sidebarBackdrop:sidebarBackdrop.backdropFilter || sidebarBackdrop.webkitBackdropFilter || 'none'
  },
  toolbar: {
    backdrop:toolbarStyle.backdropFilter || toolbarStyle.webkitBackdropFilter || 'none',
    primaryDisplay:toolbarPrimary.display, secondaryDisplay:toolbarSecondary.display, tertiaryDisplay:toolbarTertiary.display, overflowDisplay:toolbarOverflow.display,
    borderWidth:parseFloat(toolbarStyle.borderTopWidth)
  },
  cardBorderWidth:parseFloat(cardStyle.borderTopWidth),
  activeId:document.activeElement && document.activeElement.id,
  activeFocusVisible:!!(document.activeElement && document.activeElement.matches && document.activeElement.matches(':focus-visible')),
  activeOutline:document.activeElement ? getComputedStyle(document.activeElement).outlineWidth : '0px'
};
""" % json.dumps(TARGET_IDS)


def state(sid: str) -> dict[str, Any]:
    value = execute(sid, STATE_JS)
    require(isinstance(value, dict), f"could not read Structure state: {value!r}")
    return value


def require_no_overflow(s: dict[str, Any]) -> None:
    width = int(s.get("width", 0))
    require(int(s.get("scrollWidth", width + 2)) <= width + 1, f"document horizontal overflow: {s}")


def visible(rect: dict[str, Any]) -> bool:
    return rect.get("display") != "none" and rect.get("visibility") != "hidden" and float(rect.get("w", 0)) > 0 and float(rect.get("h", 0)) > 0


def validate_targets(s: dict[str, Any]) -> None:
    for name, rect in s.get("targets", {}).items():
        require(isinstance(rect, dict), f"missing target {name}")
        if visible(rect):
            require(float(rect.get("w", 0)) >= 48 and float(rect.get("h", 0)) >= 48, f"48 px target floor drifted for {name}: {rect}")


def validate_semantics(s: dict[str, Any], require_dock_frost: bool = True) -> None:
    require(s.get("ready") == "complete", f"page not ready: {s}")
    require(s["card"]["selected"] == "true" and s["card"]["pressed"] == "true", f"Card selected semantics drifted: {s['card']}")
    require(s["card"]["markerOpacity"] > .9 and s["card"]["borderInlineStart"] >= 3, f"Card selected non-color cue missing: {s['card']}")
    require(s["list"]["selectedId"] and s["list"]["markerOpacity"] > .9 and s["list"]["borderInlineStart"] >= 3, f"List selected structural cue missing: {s['list']}")
    require(s["table"]["selectedBorder"] >= 3 and s["table"]["rowMarkerWidth"] > 0, f"Table selected row structural cue missing: {s['table']}")
    require(s["table"]["wrapOverflowX"] in {"auto", "scroll"}, f"Table wrapper no longer owns horizontal overflow: {s['table']}")
    require(s["tabs"]["selectedId"] and s["tabs"]["indicatorHeight"] >= 3, f"Tab selected indicator missing: {s['tabs']}")
    require(s["navigation"]["sidebarCurrent"] and s["navigation"]["sidebarBorderInlineStart"] >= 3, f"Sidebar current-location structural cue missing: {s['navigation']}")
    require(s["navigation"]["railCurrent"] and s["navigation"]["dockCurrent"], f"Rail/Dock current-location semantics missing: {s['navigation']}")
    if s["navigation"]["railDisplay"] != "none":
        require(s["navigation"]["railShadow"] != "none" or s["navigation"]["railOutline"] >= 2, f"Navigation Rail current structural cue missing: {s['navigation']}")
    require(s["navigation"]["dockShadow"] != "none" or s["navigation"]["dockOutline"] >= 2, f"Dock current structural cue missing: {s['navigation']}")
    require(s["card"]["backdrop"] == "none" and s["list"]["backdrop"] == "none" and s["table"]["backdrop"] == "none", f"durable Card/List/Table acquired backdrop blur: {s}")
    require(s["navigation"]["sidebarBackdrop"] == "none" and s["toolbar"]["backdrop"] == "none", f"persistent Sidebar/Toolbar acquired backdrop blur: {s}")
    if require_dock_frost:
        require(s["navigation"]["dockBackdrop"] != "none", f"bounded floating Dock lost Frost in Full profile: {s['navigation']}")


def seconds(value: str) -> list[float]:
    result: list[float] = []
    for part in value.split(","):
        match = re.fullmatch(r"\s*([0-9.]+)(ms|s)\s*", part)
        if match:
            number = float(match.group(1))
            result.append(number / 1000 if match.group(2) == "ms" else number)
    return result


def set_selected_card(sid: str) -> None:
    execute(sid, "const c=document.getElementById('card-interactive'); c.dataset.selected='true'; c.setAttribute('aria-pressed','true'); return true;")


def keyboard_acceptance(sid: str) -> None:
    navigate(sid)
    media(sid, [])
    viewport(sid, 1280, 1200)
    execute(sid, "document.documentElement.dataset.glzAppearance='light'; document.documentElement.dir=''; return true;")

    press_key(sid, "\ue004")
    focused = state(sid)
    require(focused["activeId"] == "card-interactive" and focused["activeFocusVisible"] is True and float(str(focused["activeOutline"]).replace("px", "") or 0) > 0, f"keyboard focus is not visibly established on Card: {focused['activeId']}, {focused['activeOutline']}")
    press_key(sid, "\ue007")
    time.sleep(.2)
    card = state(sid)["card"]
    require(card["selected"] == "true" and card["pressed"] == "true" and card["borderInlineStart"] >= 3, f"Enter did not toggle Card into settled selected state: {card}")

    execute(sid, "document.getElementById('list-overview').focus(); return true;")
    press_key(sid, "\ue015")
    list_state = state(sid)["list"]
    require(list_state["selectedId"] == "list-activity" and state(sid)["activeId"] == "list-activity", f"ArrowDown did not move List selection/focus: {list_state}")

    execute(sid, "document.getElementById('table-sort').focus(); return true;")
    press_key(sid, "\ue007")
    require(state(sid)["table"]["sort"] == "ascending", f"Enter did not update Table aria-sort: {state(sid)['table']}")

    execute(sid, "document.getElementById('tab-overview').focus(); return true;")
    press_key(sid, "\ue014")
    tabs = state(sid)["tabs"]
    require(tabs["selectedId"] == "tab-events" and state(sid)["activeId"] == "tab-events", f"ArrowRight did not move Tabs selection/focus: {tabs}")

    for target, expected, field in (
        ("sidebar-files", "sidebar-files", "sidebarCurrent"),
        ("rail-files", "rail-files", "railCurrent"),
        ("dock-search", "dock-search", "dockCurrent"),
    ):
        execute(sid, f"document.getElementById('{target}').focus(); return true;")
        press_key(sid, "\ue007")
        current = state(sid)["navigation"][field]
        require(current == expected, f"Enter did not update {field}: {current!r}")

    execute(sid, "const b=document.getElementById('toolbar-primary'); b.dataset.activationCount='0'; b.addEventListener('click',()=>b.dataset.activationCount=String(Number(b.dataset.activationCount||'0')+1),{once:true}); b.focus(); return true;")
    press_key(sid, "\ue007")
    count = execute(sid, "return document.getElementById('toolbar-primary').dataset.activationCount")
    require(count == "1", f"Enter did not activate Toolbar priority-one action: {count!r}")


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
        set_selected_card(sid)

        for appearance in ("light", "dark", "deep-dark"):
            execute(sid, f"document.documentElement.dataset.glzAppearance='{appearance}'; return true;")
            current = state(sid)
            validate_targets(current)
            validate_semantics(current)
            require_no_overflow(current)
            screenshot(sid, appearance)

        execute(sid, "document.documentElement.dataset.glzTransparency='reduced'; return true;")
        reduced = state(sid)
        validate_targets(reduced)
        validate_semantics(reduced, require_dock_frost=False)
        require(reduced["navigation"]["dockBackdrop"] == "none", f"Reduced Transparency retained Dock backdrop: {reduced['navigation']}")
        require_no_overflow(reduced)
        execute(sid, "delete document.documentElement.dataset.glzTransparency; return true;")

        execute(sid, "document.documentElement.dataset.mode='increased-contrast'; return true;")
        contrast = state(sid)
        require(contrast["cardBorderWidth"] >= 2 and contrast["toolbar"]["borderWidth"] >= 2, f"Increased Contrast did not strengthen Structure boundaries: {contrast}")
        execute(sid, "delete document.documentElement.dataset.mode; return true;")

        media(sid, [{"name": "prefers-reduced-motion", "value": "reduce"}])
        reduced_motion = state(sid)
        durations = seconds(str(reduced_motion["card"]["transition"]))
        require(durations and max(durations) == 0, f"Reduced Motion retained interactive Card transition: {reduced_motion['card']['transition']}")
        media(sid, [])

        execute(sid, "document.documentElement.dir='ltr'; return true;")
        ltr = state(sid)
        execute(sid, "document.documentElement.dir='rtl'; return true;")
        rtl = state(sid)
        validate_targets(rtl)
        validate_semantics(rtl)
        require_no_overflow(rtl)
        require(ltr["navigation"]["sidebarLeft"] > ltr["navigation"]["sidebarRight"] and rtl["navigation"]["sidebarRight"] > rtl["navigation"]["sidebarLeft"], f"logical Sidebar current marker did not mirror in RTL: LTR={ltr['navigation']}, RTL={rtl['navigation']}")
        require(ltr["list"]["borderLeft"] > ltr["list"]["borderRight"] and rtl["list"]["borderRight"] > rtl["list"]["borderLeft"], f"logical List selection marker did not mirror in RTL: LTR={ltr['list']}, RTL={rtl['list']}")
        execute(sid, "document.documentElement.dir=''; return true;")

        media(sid, [{"name": "forced-colors", "value": "active"}])
        forced = state(sid)
        validate_targets(forced)
        require(forced["card"]["borderInlineStart"] >= 3 and forced["list"]["borderInlineStart"] >= 3 and forced["table"]["selectedBorder"] >= 3 and forced["tabs"]["indicatorHeight"] >= 3, f"Forced Colors lost selected structural cues: {forced}")
        require((forced["navigation"]["railDisplay"] == "none" or forced["navigation"]["railOutline"] >= 2) and forced["navigation"]["dockOutline"] >= 2, f"Forced Colors lost current-location outlines: {forced['navigation']}")
        require(forced["navigation"]["dockBackdrop"] == "none", f"Forced Colors retained Dock backdrop: {forced['navigation']}")
        require_no_overflow(forced)
        screenshot(sid, "forced-colors")
        media(sid, [])

        viewport(sid, 640, 1000)
        responsive = state(sid)
        validate_targets(responsive)
        require_no_overflow(responsive)
        require(responsive["navigation"]["railDisplay"] == "none", f"Navigation Rail did not transform away at 640 px: {responsive['navigation']}")
        require(responsive["toolbar"]["primaryDisplay"] != "none" and responsive["toolbar"]["secondaryDisplay"] == "none" and responsive["toolbar"]["tertiaryDisplay"] == "none" and responsive["toolbar"]["overflowDisplay"] != "none", f"Toolbar priority/overflow transformation drifted at 640 px: {responsive['toolbar']}")
        screenshot(sid, "responsive-640")

        viewport(sid, 390, 900)
        execute(sid, "document.documentElement.dataset.glzTextScale='200'; document.documentElement.style.fontSize='200%'; document.documentElement.dataset.glzAppearance='light'; return true;")
        compact = state(sid)
        validate_targets(compact)
        require_no_overflow(compact)
        require(compact["table"]["tableScrollWidth"] > compact["table"]["wrapClientWidth"], f"compact Table no longer keeps overflow local: {compact['table']}")
        require(compact["toolbar"]["primaryDisplay"] != "none" and compact["toolbar"]["overflowDisplay"] != "none", f"compact Toolbar lost priority-one/overflow access: {compact['toolbar']}")
        screenshot(sid, "compact-200")

        execute(sid, "delete document.documentElement.dataset.glzTextScale; document.documentElement.style.fontSize=''; return true;")
        keyboard_acceptance(sid)

        report = {
            "status": "pass",
            "version": "1.2.0-candidate",
            "reference": REFERENCE,
            "components": EXPECTED_COMPONENTS,
            "boundaries": ["web-reference-only", "no-native-parity-claim", "no-complete-state-token-claim", "v1.1-remains-stable"],
        }
        (ARTIFACTS / "glaze-v1.2-structure-components-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("GLAZE UI V1.2 Structure components rendered validation: PASS")
        return 0
    except Exception as error:
        print(f"GLAZE UI V1.2 Structure components rendered validation failed: {error}")
        return 1
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
                except subprocess.TimeoutExpired:
                    process.kill()


if __name__ == "__main__":
    raise SystemExit(main())

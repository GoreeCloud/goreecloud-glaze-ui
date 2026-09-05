#!/usr/bin/env python3
"""Rendered acceptance for bounded GLAZE UI V1.2 System Shell and Navigation behavior."""
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
WEB_PORT = 8799
DRIVER_PORT = 9549
SERVER = f"http://{HOST}:{WEB_PORT}"
DRIVER = f"http://{HOST}:{DRIVER_PORT}"
REFERENCE = "reference/v1.2/system-shell-navigation.html"
CONTRACT = ROOT / "contracts/v1.2/system-shell-navigation.candidate.json"
CSS = ROOT / "css/glaze-v1.2-system-shell-navigation.candidate.css"
ENTRYPOINT = ROOT / "css/glaze-v1.2.0-candidate.css"
WORKFLOW = ROOT / ".github/workflows/glaze-v1.2-system-shell-navigation.yml"
INHERITED = ROOT / "contracts/system-shell/glaze-system-shell-v1.json"
MATERIAL = ROOT / "contracts/v1.2/system-shell-materials.candidate.json"
FORM_FACTOR = ROOT / "contracts/v1.2/form-factor-tokens.candidate.json"
FORM_FACTOR_OWNER = ROOT / "tokens/glaze-v1.2-form-factor.candidate.json"
SIGNATURE = ROOT / "contracts/v1.2/signature-components.candidate.json"
EXPECTED_REGIONS = ["workspace", "navigation", "universal-search", "control-center", "critical-system"]
EXPECTED_DESTINATIONS = ["home", "search", "files", "apps"]
SEMANTIC_LAYOUTS = ["expanded", "medium", "compact", "largeFarView"]
RENDERED_LAYOUTS = ["expanded", "medium", "compact", "large"]
EXPECTED_MAPPING = dict(zip(SEMANTIC_LAYOUTS, RENDERED_LAYOUTS))


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
    paths = (CONTRACT, CSS, ENTRYPOINT, WORKFLOW, ROOT / REFERENCE, INHERITED, MATERIAL, FORM_FACTOR, FORM_FACTOR_OWNER, SIGNATURE)
    for path in paths:
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")

    contract = load(CONTRACT)
    inherited = load(INHERITED)
    material = load(MATERIAL)
    form_factor = load(FORM_FACTOR)
    owner = load(FORM_FACTOR_OWNER)
    signature = load(SIGNATURE)

    require(contract.get("version") == "1.2.0-candidate", "shell behavior contract version drifted")
    require(contract.get("lifecycle") == "candidate" and contract.get("consumerEligible") is False, "shell behavior Candidate boundary drifted")
    require(contract.get("stableBaseline") == "1.1.0", "shell behavior Stable baseline drifted")
    require(contract.get("status") == "bounded-system-shell-navigation-behavior", "shell behavior status drifted")
    require(contract.get("shellRegions") == EXPECTED_REGIONS, "shell behavior region set/order drifted")
    require(inherited.get("regions") == EXPECTED_REGIONS, "inherited shell region authority drifted")
    require(set(material.get("regions", {})) == set(EXPECTED_REGIONS), "material shell region authority drifted")
    require(form_factor.get("rules", {}).get("consumerClaimBlocked") is True, "form-factor Candidate consumer boundary drifted")
    require(owner.get("rules", {}).get("consumerClaimBlockedUntilGovernedPromotion") is True, "form-factor token-owner consumer boundary drifted")
    require(signature.get("runtimeBoundary", {}).get("pointerDestructiveConfirmationMustNotResetBetweenConsecutiveActivations") is True, "destructive search confirmation authority drifted")

    rules = contract.get("rules", {})
    for key in (
        "shellFramesApplicationWithoutDominating",
        "stableSpatialMemoryRequired",
        "predictionMayNotReorderPrimaryNavigation",
        "currentDestinationRequiresStructuralCue",
        "currentDestinationCannotDependOnColorAlone",
        "applicationIdentityDistinctFromAccountIdentity",
        "globalAndLocalActionsRemainDistinct",
        "platformNativeWindowControlsPreferredWhereApplicable",
        "criticalStateProducerAuthoritative",
        "universalSearchScopeVisible",
        "destructiveSearchActionRequiresConfirmation",
        "searchGeneratedResultsDistinctFromSystemTruth",
        "viewportWidthIsNotCanonicalDeviceIdentity",
        "platformAdapterOwnsCompositionClassSelection",
        "noNewMaterialCalibration",
        "noNewNumericSpatialCalibration",
    ):
        require(rules.get(key) is True, f"shell behavior rule drifted: {key}")
    require(rules.get("criticalDecisionsBackdropDependent") is False, "critical shell decisions may not depend on backdrop")
    require(rules.get("denseNotificationHistoryBackdropDependent") is False, "notification history may not depend on backdrop")

    composition = contract.get("composition", {})
    require(list(composition) == SEMANTIC_LAYOUTS, "shell semantic composition state set/order drifted")
    require(composition["compact"].get("majorDestinationCount") == {"minimum": 3, "maximum": 5}, "compact destination-count boundary drifted")
    require(composition["compact"].get("safeAreaAware") is True, "compact safe-area rule missing")
    require(composition["largeFarView"].get("minimumInteractiveTargetPx") == 56, "far-view target floor drifted")

    mapping = contract.get("renderedLayoutClassMapping", {})
    require(mapping.get("source") == "tokens/glaze-v1.2-form-factor.candidate.json#/compositionStates", "shell rendered-layout mapping authority drifted")
    require(mapping.get("semanticToRendered") == EXPECTED_MAPPING, "shell semantic-to-rendered mapping drifted")
    owner_states = owner.get("compositionStates", {})
    owner_mapping = {key: owner_states.get(key, {}).get("layoutClass") for key in SEMANTIC_LAYOUTS}
    require(owner_mapping == EXPECTED_MAPPING, f"form-factor token-owner mapping drifted: {owner_mapping}")

    communication = contract.get("systemCommunication", {})
    require(communication.get("notificationRequiredFields") == ["source", "event", "time", "priority", "available-action-when-applicable"], "notification field contract drifted")
    require(communication.get("criticalFailureCannotBeToastOnly") is True, "critical toast-only prohibition missing")
    require(communication.get("routineStatusCannotFlashOrPulseContinuously") is True, "routine status animation prohibition missing")

    acceptance = contract.get("acceptance", {})
    require(acceptance.get("layoutClasses") == SEMANTIC_LAYOUTS, "shell semantic acceptance states drifted")
    require(acceptance.get("layoutClassesAreSemanticCompositionStates") is True, "shell semantic/rendered distinction missing")
    require(acceptance.get("renderedLayoutClassValues") == RENDERED_LAYOUTS, "shell rendered acceptance values drifted")
    require(acceptance.get("minimumInteractiveTargetPx") == 48 and acceptance.get("farViewMinimumInteractiveTargetPx") == 56, "shell target acceptance drifted")
    require(acceptance.get("textScalePercent") == 200, "shell text-scale acceptance drifted")
    require(acceptance.get("canonicalLayerMayContainViewportBreakpoints") is False, "canonical shell behavior permits viewport breakpoints")

    compatibility = contract.get("compatibilityBoundary", {})
    require(compatibility.get("legacyViewportMediaFallbackRemainsPresent") is True, "legacy shell fallback boundary drifted")
    require(compatibility.get("legacyViewportMediaFallbackIsCanonicalCompositionAuthority") is False, "legacy viewport fallback became canonical")
    require(compatibility.get("canonicalBehaviorLayerUsesExplicitLayoutClasses") is True, "explicit layout-class authority missing")
    require(compatibility.get("renderedLayoutClassMappingConsumesFormFactorTokenOwner") is True, "shell does not consume form-factor mapping authority")
    require(compatibility.get("legacyFallbackRemovalRequiredBeforeStable") is True, "Stable cleanup requirement missing")

    css = CSS.read_text(encoding="utf-8")
    lowered = css.lower()
    require("@media (max-width" not in lowered and "@media (min-width" not in lowered, "canonical shell layer contains viewport breakpoint authority")
    require("blur(" not in lowered, "shell behavior layer introduced material blur calibration")
    require('[data-glz-layout-class="largeFarView"]' not in css, "semantic far-view state leaked into rendered CSS class authority")
    for marker in (
        '[data-glz-layout-class="expanded"]',
        '[data-glz-layout-class="medium"]',
        '[data-glz-layout-class="compact"]',
        '[data-glz-layout-class="large"]',
        'env(safe-area-inset-bottom)',
        '.glz12-shell-destination[aria-current="page"]::before',
        '.glz12-shell-notification-history',
        'backdrop-filter: none',
        '@media (forced-colors: active)',
    ):
        require(marker in css, f"shell behavior CSS marker missing: {marker}")

    reference = (ROOT / REFERENCE).read_text(encoding="utf-8")
    represented = re.findall(r'data-glz-shell-region="([^"]+)"', reference)
    require(represented == EXPECTED_REGIONS, f"shell behavior reference region set/order drifted: {represented}")
    destinations = re.findall(r'data-destination="([^"]+)"', reference)
    require(destinations == EXPECTED_DESTINATIONS, f"shell primary destination order drifted: {destinations}")
    for marker in (
        'Application: Files', 'Account: Alex', 'id="search-scope"', 'System truth · Files',
        'Generated suggestion · review before use', 'id="notifications"', 'Source: GoreeCloud Sync',
        'Priority: Routine', 'Authoritative source: Wardveil Security', 'Review required action',
    ):
        require(marker in reference, f"shell behavior reference marker missing: {marker}")

    entry = ENTRYPOINT.read_text(encoding="utf-8")
    chain = [
        '@import url("./glaze-v1.2-system-shell.candidate.css")',
        '@import url("./glaze-v1.2-system-shell-navigation.candidate.css")',
        '@import url("./glaze-v1.2-optical.candidate.css")',
    ]
    require(all(item in entry for item in chain), "Candidate entrypoint missing shell behavior import chain")
    require([entry.index(item) for item in chain] == sorted(entry.index(item) for item in chain), "shell behavior import order drifted")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    require("validate_glaze_v1_2_system_shell_navigation_rendered.py" in workflow, "shell behavior workflow does not invoke rendered validator")
    require("github.event.pull_request.head.sha || github.sha" in workflow, "shell behavior workflow is not exact-head pinned")


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
    value = request("POST", "/session", {"capabilities": {"alwaysMatch": {"browserName": "chrome", "goog:chromeOptions": {"args": ["--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-background-networking", "--disable-component-update", "--disable-extensions", "--disable-sync", "--metrics-recording-only", "--no-first-run", "--window-size=1280,1100"]}}}}, timeout=60)
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
    raise AcceptanceError("system shell behavior reference did not finish loading")


def screenshot(sid: str, name: str) -> None:
    encoded = request("GET", f"/session/{sid}/screenshot")
    require(isinstance(encoded, str) and encoded, "no screenshot bytes")
    ARTIFACTS.mkdir(exist_ok=True)
    path = ARTIFACTS / f"glaze-v1.2-system-shell-navigation-{name}.png"
    path.write_bytes(base64.b64decode(encoded))
    require(path.stat().st_size > 7000, f"invalid screenshot {path}")


STATE_JS = r"""
const root=document.getElementById('shell-reference');
const nav=document.getElementById('shell-navigation');
const current=nav.querySelector('[aria-current="page"]');
const cue=getComputedStyle(current,'::before');
const navigation=[...nav.querySelectorAll('[data-destination]')].map(e=>e.dataset.destination);
const regions=[...document.querySelectorAll('[data-glz-shell-region]')].map(e=>e.dataset.glzShellRegion);
const interactive=[...root.querySelectorAll('a,button,input,select,textarea')].filter(e=>getComputedStyle(e).display!=='none').map(e=>{const r=e.getBoundingClientRect();return {tag:e.tagName,w:r.width,h:r.height,name:e.getAttribute('aria-label')||e.textContent.trim().replace(/\s+/g,' ').slice(0,48)};});
const notification=getComputedStyle(document.getElementById('notifications'));
const critical=getComputedStyle(document.getElementById('critical'));
const searchScope=document.getElementById('search-scope').getBoundingClientRect();
const workspace=document.querySelector('.glz12-shell-behavior-workspace').getBoundingClientRect();
const side=document.querySelector('.glz12-shell-behavior-side').getBoundingClientRect();
const navRect=nav.getBoundingClientRect();
return {
  ready:document.readyState,width:innerWidth,scrollWidth:document.documentElement.scrollWidth,
  layout:root.dataset.glzLayoutClass,navigation,regions,navDirection:getComputedStyle(nav).flexDirection,
  cue:{width:parseFloat(cue.width)||0,height:parseFloat(cue.height)||0,display:cue.display},interactive,
  notificationBackdrop:notification.backdropFilter||notification.webkitBackdropFilter||'none',
  criticalBackdrop:critical.backdropFilter||critical.webkitBackdropFilter||'none',
  searchScope:{width:searchScope.width,height:searchScope.height},
  positions:{workspaceTop:workspace.top,workspaceBottom:workspace.bottom,sideTop:side.top,sideBottom:side.bottom,navTop:navRect.top,navBottom:navRect.bottom},
  textScale:document.documentElement.dataset.glzTextScale||'',transparency:document.documentElement.dataset.glzTransparency||'',dir:document.documentElement.dir||'ltr'
};
"""


def state(sid: str) -> dict[str, Any]:
    value = execute(sid, STATE_JS)
    require(isinstance(value, dict), f"could not read system shell state: {value!r}")
    return value


def identity(value: dict[str, Any], width: int, minimum_target: int) -> None:
    require(value.get("ready") == "complete", f"system shell page not complete: {value}")
    require(abs(int(value.get("width", 0)) - width) <= 1, f"system shell viewport mismatch: {value}")
    require(int(value.get("scrollWidth", width + 2)) <= width + 1, f"system shell page has horizontal overflow: {value}")
    require(value.get("navigation") == EXPECTED_DESTINATIONS, f"system shell primary navigation order drifted: {value}")
    require(value.get("regions") == EXPECTED_REGIONS, f"system shell region set/order drifted: {value}")
    require(max(float(value["cue"]["width"]), float(value["cue"]["height"])) >= 3, f"current location lacks structural cue: {value}")
    require(float(value["searchScope"]["width"]) > 0 and float(value["searchScope"]["height"]) > 0, f"search scope is not visibly discoverable: {value}")
    require(value.get("notificationBackdrop") == "none", f"notification history became backdrop-dependent: {value}")
    require(value.get("criticalBackdrop") == "none", f"critical state became backdrop-dependent: {value}")
    small = [item for item in value.get("interactive", []) if float(item.get("w", 0)) < minimum_target or float(item.get("h", 0)) < minimum_target]
    require(not small, f"interactive target floor {minimum_target}px drifted: {small}")


def set_layout(sid: str, layout: str) -> None:
    execute(sid, f"document.getElementById('shell-reference').dataset.glzLayoutClass={json.dumps(layout)};return true;")


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
        viewport(sid, 1280, 1100)
        navigate(sid)

        expanded = state(sid)
        identity(expanded, 1280, 48)
        require(expanded.get("layout") == "expanded" and expanded.get("navDirection") == "column", f"expanded shell composition drifted: {expanded}")
        screenshot(sid, "expanded")

        set_layout(sid, "medium")
        medium = state(sid)
        identity(medium, 1280, 48)
        require(medium.get("layout") == "medium" and medium.get("navDirection") == "column", f"medium navigation rail drifted: {medium}")
        require(float(medium["positions"]["sideTop"]) >= float(medium["positions"]["workspaceBottom"]) - 1, f"medium control region did not transform after workspace: {medium}")

        viewport(sid, 390, 1100)
        execute(sid, "document.documentElement.dataset.glzTextScale='200';document.getElementById('shell-reference').dataset.glzLayoutClass='compact';return true;")
        compact = state(sid)
        identity(compact, 390, 48)
        require(compact.get("layout") == "compact" and compact.get("navDirection") == "row", f"compact bottom navigation drifted: {compact}")
        require(compact.get("textScale") == "200", f"compact 200% text state missing: {compact}")
        require(float(compact["positions"]["navTop"]) >= float(compact["positions"]["sideBottom"]) - 1, f"compact navigation is not after task/control content: {compact}")
        screenshot(sid, "compact-200")

        viewport(sid, 1280, 1100)
        execute(sid, "document.documentElement.dataset.glzTextScale='';document.getElementById('shell-reference').dataset.glzLayoutClass='large';return true;")
        far_view = state(sid)
        identity(far_view, 1280, 56)
        require(far_view.get("layout") == "large" and far_view.get("navDirection") == "column", f"far-view rendered layout mapping drifted: {far_view}")
        screenshot(sid, "large-far-view")

        viewport(sid, 390, 1100)
        execute(sid, "document.getElementById('shell-reference').dataset.glzLayoutClass='compact';document.documentElement.dataset.glzTextScale='200';document.documentElement.dataset.glzTransparency='reduced';document.documentElement.dir='rtl';return true;")
        reduced = state(sid)
        identity(reduced, 390, 48)
        require(reduced.get("transparency") == "reduced" and reduced.get("dir") == "rtl", f"reduced-transparency/RTL state missing: {reduced}")
        media(sid, [{"name": "forced-colors", "value": "active"}])
        forced = state(sid)
        identity(forced, 390, 48)
        screenshot(sid, "forced-colors-rtl")

        print("GLAZE UI V1.2 System Shell and Navigation behavior validated: semantic-to-rendered form-factor mapping, stable navigation, search scope, notifications, critical state, and accessibility gates PASS")
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
        print(f"GLAZE UI V1.2 System Shell and Navigation acceptance failed: {error}")
        raise SystemExit(1)

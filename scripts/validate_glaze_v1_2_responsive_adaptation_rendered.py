#!/usr/bin/env python3
"""Exact-head rendered acceptance for bounded GLAZE UI V1.2 Responsive and Form-Factor Adaptation Candidate."""
from __future__ import annotations

import base64, json, shutil, subprocess, sys, time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
HOST, WEB_PORT, DRIVER_PORT = "127.0.0.1", 8797, 9547
SERVER, DRIVER = f"http://{HOST}:{WEB_PORT}", f"http://{HOST}:{DRIVER_PORT}"
REFERENCE = "reference/v1.2/responsive-adaptation.html"
CONTRACT = ROOT / "contracts/v1.2/responsive-adaptation-reference.candidate.json"
CSS = ROOT / "css/glaze-v1.2-responsive-adaptation-reference.candidate.css"
RUNTIME = ROOT / "js/glaze-v1.2-responsive-adaptation-reference.candidate.mjs"
ENTRYPOINT = ROOT / "css/glaze-v1.2.0-candidate.css"
FORM_FACTOR_CONTRACT = ROOT / "contracts/v1.2/form-factor-tokens.candidate.json"
FORM_FACTOR_TOKENS = ROOT / "tokens/glaze-v1.2-form-factor.candidate.json"
SCENES = ["320-mobile","modern-mobile-portrait","mobile-landscape","tablet-portrait","tablet-landscape","narrow-desktop","standard-desktop","ultra-wide-desktop","folded-foldable","unfolded-foldable","tv-far-view","wearable","reduced-transparency","text-scale-200","rtl"]
MAPPING = {"320-mobile":"compact","modern-mobile-portrait":"compact","mobile-landscape":"medium","tablet-portrait":"medium","tablet-landscape":"medium","narrow-desktop":"compact","standard-desktop":"expanded","ultra-wide-desktop":"expanded","folded-foldable":"compact","unfolded-foldable":"medium","tv-far-view":"large","wearable":"wearable","reduced-transparency":"expanded","text-scale-200":"compact","rtl":"expanded"}

class AcceptanceError(RuntimeError): pass

def require(ok: bool, message: str) -> None:
    if not ok: raise AcceptanceError(message)

def read_json(path: Path) -> dict[str, Any]: return json.loads(path.read_text(encoding="utf-8"))

def validate_source() -> None:
    for path in (CONTRACT,CSS,RUNTIME,ENTRYPOINT,FORM_FACTOR_CONTRACT,FORM_FACTOR_TOKENS,ROOT / REFERENCE): require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    c, fc, ft = read_json(CONTRACT), read_json(FORM_FACTOR_CONTRACT), read_json(FORM_FACTOR_TOKENS)
    require(c.get("version") == "1.2.0-candidate" and c.get("lifecycle") == "candidate" and c.get("consumerEligible") is False and c.get("stableBaseline") == "1.1.0", "Responsive lifecycle boundary drifted")
    require(c.get("referenceScenes") == SCENES and c.get("layoutClassMapping") == MAPPING, "Responsive scene/mapping contract drifted")
    require(c.get("semanticCompositionStateForFarView") == "largeFarView", "Far-view semantic state drifted")
    b = c.get("authorityBoundary", {})
    require(b.get("introducesNewFormFactorTokenOwner") is False and b.get("introducesDeviceBrandBreakpoints") is False and b.get("runtimeInfersDeviceIdentity") is False and b.get("runtimeSelectsProductionCapabilityClass") is False and b.get("platformAdapterRemainsCapabilitySelectionAuthority") is True, "Responsive authority boundary drifted")
    rules = c.get("rules", {})
    for key in ("widthIsNotDeviceIdentity","capabilityInputsExtendBeyondWidth","mobileIsFirstClass","desktopSqueezedIntoMobileProhibited","semanticTaskPreservedAcrossRecomposition","currentLocationPreservedAcrossRecomposition","importantStatePreservedAcrossRecomposition","userEnteredDataPreservedAcrossRecomposition","selectionPreservedAcrossRecomposition","focusPreservedWherePractical","scrollContextPreservedWherePractical","recompositionMustNotRequirePageReload","safeAreaInsetsAreFunctionalConstraints","keyboardOcclusionIsFunctionalConstraint","wideTablesDoNotCausePageHorizontalScroll","compactTablesMayTransformToStructuredLists","foldPostureMayChangeCompositionWithoutChangingTask","farViewUsesAtLeast56PxClassTargets","wearablePrioritizesGlanceablePrimaryValue","touchAndPointerCanCoexistWithoutTouchIncompleteness","reducedTransparencyPreservesMeaning","textScale200PreservesCoreTask","rtlUsesLogicalLayout","noRuntimeNetworkRequest","noRuntimePersistence","noNewCanonicalComponent","noNewMaterialCalibration"): require(rules.get(key) is True, f"Responsive rule drifted: {key}")
    a = c.get("interactiveAcceptance", {})
    require(a.get("minimumInteractiveTargetPx") == 48 and a.get("farViewMinimumInteractiveTargetPx") == 56 and a.get("narrowWebWidthPx") == 320 and a.get("platformSpecificEvidenceRequiredForProductionClaims") is True, "Responsive acceptance boundary drifted")
    require(fc.get("compositionClasses") == ["compact","medium","expanded","largeFarView","wearable","spatial"], "Form-factor semantic classes drifted")
    require(fc.get("rules", {}).get("platformAdapterSelectsCapabilityClass") is True and fc.get("rules", {}).get("consumerClaimBlocked") is True, "Form-factor authority/claim boundary drifted")
    lf = ft.get("compositionStates", {}).get("largeFarView", {})
    require(lf.get("layoutClass") == "large" and lf.get("minimumInteractiveTargetPx") == 56, "Authoritative far-view mapping drifted")
    require(ft.get("acceptanceBoundaries", {}).get("minimumInteractiveTargetPx") == 48 and ft.get("acceptanceBoundaries", {}).get("narrowWebWidthClassPx") == 320, "Authoritative size boundary drifted")
    ref = (ROOT / REFERENCE).read_text(encoding="utf-8")
    require([x.split('"',1)[0] for x in ref.split('data-adaptation-scene="')[1:]] == SCENES, "Responsive reference scene order drifted")
    for marker in ("Width is not device identity","320 px-class mobile","Modern mobile portrait","Narrow desktop","continuity-workspace","Folded foldable","Unfolded foldable","TV / far-view","Wearable","Reduced Transparency","200% text","RTL","Preserve me","record Alpha","no scenario on this page establishes native or physical-device acceptance"): require(marker in ref, f"Responsive reference marker missing: {marker}")
    css = CSS.read_text(encoding="utf-8")
    require("blur(" not in css.lower() and "@media (max-width" not in css and "@media (min-width" not in css, "Responsive reference introduced material/breakpoint authority")
    for marker in ('[data-glz-layout-class="compact"]','[data-glz-layout-class="medium"]','[data-glz-layout-class="expanded"]','[data-glz-layout-class="large"]','[data-glz-layout-class="wearable"]','env(safe-area-inset-bottom)','data-fold-posture="unfolded"','data-glz-text-scale="200"','data-glz-transparency="reduced"','@media (forced-colors:active)','--glz12-target-min','--glz12-shell-target-assisted'): require(marker in css, f"Responsive CSS marker missing: {marker}")
    require('data-glz-type="numeric"' in ref, "Wearable numeric typography role missing")
    runtime = RUNTIME.read_text(encoding="utf-8")
    for forbidden in ("fetch(","XMLHttpRequest","WebSocket","localStorage","sessionStorage","indexedDB","navigator.sendBeacon","document.cookie"): require(forbidden not in runtime, f"Responsive runtime may not transport/persist state: {forbidden}")
    for marker in ("REFERENCE_LAYOUTS","requestAnimationFrame","preventScroll: true","data-recompose-to","data-adapt-destination","data-adapt-select","glz:reference-recomposition","fixtureOnly: true"): require(marker in runtime, f"Responsive runtime marker missing: {marker}")
    entry = ENTRYPOINT.read_text(encoding="utf-8")
    states = '@import url("./glaze-v1.2-states-feedback-recovery.candidate.css");'; responsive = '@import url("./glaze-v1.2-responsive-adaptation-reference.candidate.css");'; access = '@import url("./glaze-v1.2-accessibility.candidate.css");'
    require(all(x in entry for x in (states,responsive,access)) and entry.index(states) < entry.index(responsive) < entry.index(access), "Responsive Candidate import chain drifted")

def request(method: str, path: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> Any:
    req = Request(f"{DRIVER}{path}", data=None if payload is None else json.dumps(payload).encode(), method=method, headers={"Content-Type":"application/json; charset=utf-8"})
    try:
        with urlopen(req, timeout=timeout) as response: raw = response.read()
    except HTTPError as error: raise AcceptanceError(f"WebDriver HTTP {error.code}: {error.read().decode(errors='replace')}") from error
    except (URLError, TimeoutError) as error: raise AcceptanceError(f"WebDriver request failed: {error}") from error
    if not raw: return None
    value = json.loads(raw.decode()).get("value")
    if isinstance(value, dict) and value.get("error"): raise AcceptanceError(f"WebDriver {value.get('error')}: {value.get('message','')}")
    return value

def wait_http(url: str) -> None:
    end = time.monotonic() + 15
    while time.monotonic() < end:
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200: return
        except Exception: pass
        time.sleep(.15)
    raise AcceptanceError(f"HTTP endpoint not ready: {url}")

def chromedriver() -> str:
    for p in (shutil.which("chromedriver"),"/usr/bin/chromedriver","/usr/local/share/chromedriver-linux64/chromedriver"):
        if p and Path(p).is_file(): return str(p)
    raise AcceptanceError("chromedriver unavailable")

def execute(sid: str, script: str) -> Any: return request("POST", f"/session/{sid}/execute/sync", {"script":script,"args":[]})
def cdp(sid: str, cmd: str, params: dict[str, Any]) -> Any: return request("POST", f"/session/{sid}/goog/cdp/execute", {"cmd":cmd,"params":params})
def viewport(sid: str, width: int, height: int) -> None: cdp(sid,"Emulation.setDeviceMetricsOverride",{"width":width,"height":height,"deviceScaleFactor":1,"mobile":False,"screenWidth":width,"screenHeight":height})
def media(sid: str, features: list[dict[str,str]]) -> None: cdp(sid,"Emulation.setEmulatedMedia",{"media":"screen","features":features})

def screenshot(sid: str, name: str) -> None:
    raw = request("GET", f"/session/{sid}/screenshot"); require(isinstance(raw,str) and raw, "no screenshot bytes")
    ARTIFACTS.mkdir(exist_ok=True); p = ARTIFACTS / f"glaze-v1.2-responsive-{name}.png"; p.write_bytes(base64.b64decode(raw)); require(p.stat().st_size > 5000, f"invalid screenshot {p}")

def load(sid: str) -> None:
    request("POST",f"/session/{sid}/url",{"url":f"{SERVER}/{REFERENCE}"})
    end = time.monotonic() + 15
    while time.monotonic() < end:
        if execute(sid,"return document.readyState==='complete' && !!window.GlazeV12ResponsiveAdaptation"): return
        time.sleep(.1)
    raise AcceptanceError("Responsive reference did not initialize")

def isolate(sid: str, scene: str) -> None:
    execute(sid, f"for(const e of document.querySelectorAll('[data-adaptation-scene]'))e.hidden=e.dataset.adaptationScene!=={json.dumps(scene)};document.querySelector('.intro').hidden=true;window.scrollTo(0,0);return true;")

def targets(sid: str, selector: str) -> list[dict[str,Any]]:
    value = execute(sid, f"return [...document.querySelectorAll({json.dumps(selector)})].filter(e=>!e.hidden&&getComputedStyle(e).display!=='none'&&e.getClientRects().length).map(e=>{{const b=e.getBoundingClientRect();return{{text:e.textContent.trim().slice(0,50),w:b.width,h:b.height}}}});")
    require(isinstance(value,list), "could not read target geometry"); return value

def target_floor(items: list[dict[str,Any]], minimum: int, label: str) -> None:
    bad = [x for x in items if float(x.get("w",0)) < minimum or float(x.get("h",0)) < minimum]; require(not bad, f"{label} {minimum}px target floor drifted: {bad}")

def main() -> int:
    http = driver = None; sid = None
    try:
        validate_source(); ARTIFACTS.mkdir(exist_ok=True)
        http = subprocess.Popen([sys.executable,"-m","http.server",str(WEB_PORT),"--bind",HOST,"--directory",str(ROOT)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); wait_http(f"{SERVER}/{REFERENCE}")
        driver = subprocess.Popen([chromedriver(),f"--port={DRIVER_PORT}","--allowed-ips=127.0.0.1"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        end = time.monotonic() + 15
        while time.monotonic() < end:
            try:
                if request("GET","/status").get("ready"): break
            except Exception: pass
            time.sleep(.2)
        value = request("POST","/session",{"capabilities":{"alwaysMatch":{"browserName":"chrome","goog:chromeOptions":{"args":["--headless=new","--no-sandbox","--disable-dev-shm-usage","--disable-background-networking","--disable-component-update","--disable-extensions","--disable-sync","--no-first-run","--window-size=1280,960"]}}}},60); sid = value["sessionId"]
        media(sid,[]); viewport(sid,1280,960); load(sid)
        scenes = execute(sid,"return [...document.querySelectorAll('[data-adaptation-scene]')].map(e=>[e.dataset.adaptationScene,e.dataset.glzLayoutClass,e.dataset.inputProfile]);")
        require([r[0] for r in scenes] == SCENES and {r[0]:r[1] for r in scenes} == MAPPING, f"Rendered scene/mapping drifted: {scenes}"); screenshot(sid,"gallery-light")

        execute(sid,"const r=document.querySelector('#continuity-workspace'),i=document.querySelector('#continuity-note');i.value='User draft preserved';document.querySelector('#record-beta').click();i.focus();window.GlazeV12ResponsiveAdaptation.applyReferenceComposition(r,'compact');return true;"); time.sleep(.1)
        state = execute(sid,"const r=document.querySelector('#continuity-workspace'),i=document.querySelector('#continuity-note');return [r.dataset.glzLayoutClass,r.dataset.currentDestination,r.dataset.selectedRecord,r.dataset.fixtureState,i.value,document.activeElement?.id||''];")
        require(state == ["compact","files","beta","stale","User draft preserved","continuity-note"], f"Compact continuity failed: {state}")
        for layout in ("medium","expanded","large"):
            execute(sid,f"window.GlazeV12ResponsiveAdaptation.applyReferenceComposition(document.querySelector('#continuity-workspace'),{json.dumps(layout)});return true;"); time.sleep(.1)
            state = execute(sid,"const r=document.querySelector('#continuity-workspace'),i=document.querySelector('#continuity-note');return [r.dataset.glzLayoutClass,r.dataset.currentDestination,r.dataset.selectedRecord,r.dataset.fixtureState,i.value,document.activeElement?.id||''];")
            require(state == [layout,"files","beta","stale","User draft preserved","continuity-note"], f"{layout} continuity failed: {state}")
        screenshot(sid,"continuity-large")

        load(sid); viewport(sid,320,760); isolate(sid,"320-mobile")
        narrow = execute(sid,"const s=document.querySelector('[data-adaptation-scene=\"320-mobile\"]'),b=s.getBoundingClientRect();return [innerWidth,document.documentElement.scrollWidth,b.left,b.right,s.dataset.glzLayoutClass];")
        require(narrow[0] == 320 and narrow[1] <= 321 and narrow[2] >= -.5 and narrow[3] <= 320.5 and narrow[4] == "compact", f"320px overflow/clipping failed: {narrow}"); target_floor(targets(sid,'[data-adaptation-scene="320-mobile"] button'),48,"320px"); screenshot(sid,"320-mobile")

        load(sid); viewport(sid,1280,900); isolate(sid,"tv-far-view")
        far = execute(sid,"const s=document.querySelector('[data-adaptation-scene=\"tv-far-view\"]');return [s.dataset.glzLayoutClass,s.dataset.inputProfile];")
        require(far == ["large","directional"], f"Far-view mapping failed: {far}"); target_floor(targets(sid,'[data-adaptation-scene="tv-far-view"] button'),56,"Far-view"); screenshot(sid,"far-view")

        load(sid); viewport(sid,260,420); isolate(sid,"wearable")
        wearable = execute(sid,"const s=document.querySelector('[data-adaptation-scene=\"wearable\"]'),p=s.querySelector('[data-adapt-primary-value]'),q=s.querySelector('[data-adapt-secondary=\"true\"]'),i=s.querySelector('.glz12-adapt-inspector');return [s.dataset.glzLayoutClass,p.textContent.trim(),getComputedStyle(q).display,getComputedStyle(i).display,document.documentElement.scrollWidth,innerWidth];")
        require(wearable[0] == "wearable" and wearable[1] == "72%" and wearable[2] == "none" and wearable[3] == "none" and wearable[4] <= wearable[5] + 1, f"Wearable hierarchy failed: {wearable}"); target_floor(targets(sid,'[data-adaptation-scene="wearable"] button'),48,"Wearable")

        load(sid); viewport(sid,960,800); isolate(sid,"reduced-transparency")
        reduced = execute(sid,"document.documentElement.dataset.glzTransparency='reduced';const s=getComputedStyle(document.querySelector('[data-adaptation-scene=\"reduced-transparency\"] .glz12-adapt-region'));return [s.backdropFilter||s.webkitBackdropFilter||'none',s.boxShadow];")
        require(reduced[0] in ("none","") and reduced[1] in ("none", ""), f"Reduced Transparency failed: {reduced}")

        load(sid); viewport(sid,320,760); isolate(sid,"text-scale-200")
        large = execute(sid,"document.documentElement.dataset.glzTextScale='200';const s=document.querySelector('[data-adaptation-scene=\"text-scale-200\"]'),b=s.getBoundingClientRect();return [document.documentElement.scrollWidth,innerWidth,b.left,b.right,!!s.querySelector('input')];")
        require(large[4] and large[0] <= large[1] + 1 and large[2] >= -.5 and large[3] <= 320.5, f"200% text compact continuity failed: {large}")

        load(sid); viewport(sid,960,800); isolate(sid,"rtl")
        rtl = execute(sid,"document.documentElement.dir='rtl';const s=getComputedStyle(document.querySelector('[data-adaptation-scene=\"rtl\"] [aria-current=\"page\"]'));return [document.documentElement.dir,s.borderInlineStartWidth];")
        require(rtl[0] == "rtl" and float(rtl[1].replace("px","")) >= 3, f"RTL logical current-location cue failed: {rtl}")
        media(sid,[{"name":"forced-colors","value":"active"}]); forced = execute(sid,"return getComputedStyle(document.querySelector('[data-adaptation-scene=\"rtl\"] .glz12-adapt-region')).forcedColorAdjust;")
        require(forced == "auto", f"Forced Colors adaptation failed: {forced}")
        print("Responsive and Form-Factor Adaptation Candidate: source and rendered acceptance passed."); return 0
    except AcceptanceError as error:
        print(f"ERROR: {error}", file=sys.stderr); return 1
    finally:
        if sid:
            try: request("DELETE",f"/session/{sid}",timeout=5)
            except Exception: pass
        for process in (driver,http):
            if process:
                process.terminate()
                try: process.wait(timeout=5)
                except subprocess.TimeoutExpired: process.kill()

if __name__ == "__main__": raise SystemExit(main())

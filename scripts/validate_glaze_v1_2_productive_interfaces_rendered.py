#!/usr/bin/env python3
"""Exact-head rendered acceptance for bounded GLAZE UI V1.2 Productive Interfaces Candidate."""
from __future__ import annotations

import base64, json, re, shutil, subprocess, sys, time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
HOST, WEB_PORT, DRIVER_PORT = "127.0.0.1", 8794, 9544
SERVER, DRIVER = f"http://{HOST}:{WEB_PORT}", f"http://{HOST}:{DRIVER_PORT}"
REFERENCE = "reference/v1.2/productive-interfaces.html"
CONTRACT = ROOT / "contracts/v1.2/productive-interfaces.candidate.json"
CSS = ROOT / "css/glaze-v1.2-productive-interfaces.candidate.css"
RUNTIME = ROOT / "js/glaze-v1.2-productive-interfaces.candidate.mjs"
ENTRYPOINT = ROOT / "css/glaze-v1.2.0-candidate.css"
CATALOG = ROOT / "contracts/components/v1/catalog.json"
SCENES = ["file-browser","device-manager","service-manager","metrics-table","log-viewer","network-records","identity-administration","bulk-selection","advanced-filtering","table-inspector"]
PROPOSED = ["GlzDataGrid","GlzCommandBar","GlzFilterBar","GlzFilterChip","GlzInspector","GlzStatusCell","GlzProgressCell","GlzColumnPicker","GlzBulkActionBar","GlzLogViewer","GlzRecordList","GlzSavedView"]

class AcceptanceError(RuntimeError): pass

def require(ok: bool, message: str) -> None:
    if not ok: raise AcceptanceError(message)

def validate_source() -> None:
    for p in (CONTRACT, CSS, RUNTIME, ENTRYPOINT, CATALOG, ROOT / REFERENCE):
        require(p.is_file(), f"missing {p.relative_to(ROOT)}")
    c = json.loads(CONTRACT.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    require(c.get("version") == "1.2.0-candidate" and c.get("lifecycle") == "candidate" and c.get("consumerEligible") is False, "Productive lifecycle boundary drifted")
    require(c.get("stableBaseline") == "1.1.0", "Productive Stable baseline drifted")
    boundary = c.get("canonicalComponentBoundary", {})
    require(boundary.get("catalogExtensionIntroduced") is False and boundary.get("canonicalPrimaryComponent") == "GlzTable", "Productive canonical boundary drifted")
    require(boundary.get("proposedExtensionsRemainNonCanonical") == PROPOSED, "proposed Productive extension list drifted")
    require(c.get("referenceScenes") == SCENES, "Productive scene contract drifted")
    rules = c.get("rules", {})
    for key in ("productiveDensityIsNotMiniaturization","denseTablesUseStableSurfaces","selectedFocusedAndActiveStatesMustRemainDistinct","essentialActionsCannotRequireHover","multiSelectionCountMustBeVisible","bulkActionScopeMustBeExplicit","sortColumnAndDirectionMustRemainVisible","activeFiltersMustRemainVisible","clearFiltersMustNotResetUnrelatedSortOrDensity","searchScopeMustRemainVisible","wideTableMayScrollHorizontallyButPageMayNot","inspectorMustCorrespondToSelectedRecord","multiSelectionInspectorMustNotPretendToRepresentOneObject","unknownStateMustBeDistinctFromHealthyOfflineUnavailableAndError","indeterminateProgressCannotFabricatePercentage","staleDataMustBeVisibleWhenMaterial","partialFailureRetainsUsableDataWhereSafe","liveLogAutoScrollPausesWhenUserLeavesLiveEdge","keyboardCoreOperationRequired","touchTargetsRemainAccessibleInProductiveDensity","noRuntimeNetworkRequest","noRuntimePersistence","noNewCanonicalComponent","noNewMaterialCalibration"):
        require(rules.get(key) is True, f"Productive rule drifted: {key}")
    require(rules.get("tableLayerIntroducesBackdropBlur") is False, "Productive table layer may not introduce blur")
    data = c.get("dataAuthorityBoundary", {})
    require(data.get("referenceDataIsFixtureOnly") is True and data.get("runtimeFetchesAuthoritativeData") is False and data.get("runtimePersistsViewCustomization") is False and data.get("runtimeClaimsProducerUpdateSuccess") is False, "Productive data authority boundary drifted")

    flat = [name for names in catalog.get("tiers", {}).values() for name in names]
    require(catalog.get("componentCount") == 32 and len(flat) == 32 and len(set(flat)) == 32, "canonical component catalog drifted")
    require(not any(name in flat for name in PROPOSED), "proposed Productive components leaked into canonical catalog")

    ref = (ROOT / REFERENCE).read_text(encoding="utf-8")
    require(re.findall(r'data-productive-scene="([^"]+)"', ref) == SCENES, "Productive reference scene order drifted")
    for marker in ('canonical GlzTable','fixture data','Search scope:','data-state="unknown"','data-state="stale"','data-state="partial"','duration unknown','data-mobile-transform="structured-list"','data-log-viewer','data-inspector-title','data-selection-count','data-filter-count','aria-sort="none"'):
        require(marker in ref, f"Productive reference marker missing: {marker}")
    require(re.search(r'duration unknown[^%]{0,80}</', ref, re.I) is not None, "indeterminate reference must not fabricate a percentage")

    css = CSS.read_text(encoding="utf-8")
    require("blur(" not in css.lower(), "Productive layer must not introduce blur")
    require("@media (max-width" not in css and "@media (min-width" not in css, "Productive layer must not own viewport-width breakpoints")
    for marker in ('.glz12-productive-table','.glz12-table-scroll','overflow-x: auto','[data-glz-layout-class="compact"]','.glz12-structured-list','data-glz-touch-assistance="true"','data-glz-text-scale="200"','data-glz-transparency="reduced"','@media (forced-colors: active)'):
        require(marker in css, f"Productive CSS marker missing: {marker}")
    for token in ('--glz12-structural-border','--glz12-radius-surface','--glz12-radius-floating-control','--glz12-radius-pill','--glz12-state-focus-width','--glz12-state-focus-offset','--glz12-space-control','--glz12-target-min'):
        require(token in css, f"Productive token consumption missing: {token}")

    runtime = RUNTIME.read_text(encoding="utf-8")
    for forbidden in ("fetch(","XMLHttpRequest","WebSocket","localStorage","sessionStorage","indexedDB","navigator.sendBeacon","document.cookie"):
        require(forbidden not in runtime, f"Productive runtime may not transport/persist data: {forbidden}")
    for marker in ("data-row-select","data-select-all","aria-sort","data-filter-status","data-table-search","data-inspector-title","data-log-viewer","data-log-toggle"):
        require(marker in runtime, f"Productive runtime marker missing: {marker}")

    entry = ENTRYPOINT.read_text(encoding="utf-8")
    forms = '@import url("./glaze-v1.2-forms.candidate.css")'
    productive = '@import url("./glaze-v1.2-productive-interfaces.candidate.css")'
    access = '@import url("./glaze-v1.2-accessibility.candidate.css")'
    require(all(x in entry for x in (forms, productive, access)), "Candidate entrypoint missing Productive import chain")
    require(entry.index(forms) < entry.index(productive) < entry.index(access), "Productive import order drifted")

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
    for p in (shutil.which("chromedriver"), "/usr/bin/chromedriver", "/usr/local/share/chromedriver-linux64/chromedriver"):
        if p and Path(p).is_file(): return str(p)
    raise AcceptanceError("chromedriver unavailable")

def execute(sid: str, script: str) -> Any: return request("POST", f"/session/{sid}/execute/sync", {"script":script,"args":[]})
def cdp(sid: str, cmd: str, params: dict[str, Any]) -> Any: return request("POST", f"/session/{sid}/goog/cdp/execute", {"cmd":cmd,"params":params})
def viewport(sid: str, width: int, height: int) -> None: cdp(sid,"Emulation.setDeviceMetricsOverride",{"width":width,"height":height,"deviceScaleFactor":1,"mobile":False,"screenWidth":width,"screenHeight":height})
def media(sid: str, features: list[dict[str,str]]) -> None: cdp(sid,"Emulation.setEmulatedMedia",{"media":"screen","features":features})

def screenshot(sid: str, name: str) -> None:
    raw = request("GET", f"/session/{sid}/screenshot")
    require(isinstance(raw,str) and raw, "no screenshot bytes")
    ARTIFACTS.mkdir(exist_ok=True)
    p = ARTIFACTS / f"glaze-v1.2-productive-{name}.png"; p.write_bytes(base64.b64decode(raw)); require(p.stat().st_size > 7000, f"invalid screenshot {p}")

STATE_JS = r"""
const r=document.documentElement,lib=document.querySelector('#productive-reference'),net=document.querySelector('#scene-network-records .glz12-table-scroll'),filterTable=document.querySelector('#scene-filtering .glz12-table-scroll'),structured=document.querySelector('#scene-filtering .glz12-structured-list'),inspector=document.querySelector('#record-inspector'),log=document.querySelector('#log-viewer');
const nodes=[...document.querySelectorAll('button,input,select')].filter(e=>!e.hidden&&getComputedStyle(e).display!=='none'&&e.getClientRects().length);
return {width:innerWidth,scrollWidth:document.documentElement.scrollWidth,layout:lib.dataset.glzLayoutClass,appearance:r.dataset.glzAppearance||'',dir:r.dir||'ltr',transparency:r.dataset.glzTransparency||'',scenes:[...document.querySelectorAll('[data-productive-scene]')].map(e=>e.dataset.productiveScene),networkLocalOverflow:net.scrollWidth>net.clientWidth,filterTableDisplay:getComputedStyle(filterTable).display,structuredDisplay:getComputedStyle(structured).display,sceneBackdrop:getComputedStyle(document.querySelector('#scene-filtering')).backdropFilter||'none',inspectorBackdrop:getComputedStyle(inspector).backdropFilter||'none',logBackdrop:getComputedStyle(log).backdropFilter||'none',targets:nodes.map(e=>{const b=e.getBoundingClientRect();return{id:e.id||e.textContent.trim().slice(0,28),w:b.width,h:b.height}})};
"""

def state(sid: str) -> dict[str,Any]:
    s=execute(sid,STATE_JS); require(isinstance(s,dict),"could not read Productive state"); return s

def check_page(s: dict[str,Any], width: int, minimum: int = 48) -> None:
    require(abs(int(s.get("width",0))-width)<=1 and int(s.get("scrollWidth",width+2))<=width+1, f"Productive viewport/page overflow failure: {s}")
    require(s.get("scenes")==SCENES, f"Productive scene drifted: {s.get('scenes')}")
    bad=[x for x in s.get("targets",[]) if float(x.get("w",0))<minimum or float(x.get("h",0))<minimum]; require(not bad,f"Productive {minimum}px target floor drifted: {bad}")

def main() -> int:
    http=driver=None; sid=None
    try:
        validate_source(); ARTIFACTS.mkdir(exist_ok=True)
        http=subprocess.Popen([sys.executable,"-m","http.server",str(WEB_PORT),"--bind",HOST,"--directory",str(ROOT)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); wait_http(f"{SERVER}/{REFERENCE}")
        driver=subprocess.Popen([chromedriver(),f"--port={DRIVER_PORT}","--allowed-ips=127.0.0.1"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        end=time.monotonic()+15
        while time.monotonic()<end:
            try:
                if request("GET","/status").get("ready"): break
            except Exception: pass
            time.sleep(.2)
        value=request("POST","/session",{"capabilities":{"alwaysMatch":{"browserName":"chrome","goog:chromeOptions":{"args":["--headless=new","--no-sandbox","--disable-dev-shm-usage","--disable-background-networking","--disable-component-update","--disable-extensions","--disable-sync","--no-first-run","--window-size=1280,960"]}}}},60); sid=value["sessionId"]
        media(sid,[]); viewport(sid,1280,960); request("POST",f"/session/{sid}/url",{"url":f"{SERVER}/{REFERENCE}"})
        end=time.monotonic()+15
        while time.monotonic()<end:
            if execute(sid,"return document.readyState==='complete' && !!window.GlazeV12ProductiveInterfaces"): break
            time.sleep(.1)
        expanded=state(sid); check_page(expanded,1280); require(expanded.get("layout")=="expanded" and expanded.get("filterTableDisplay")!="none" and expanded.get("structuredDisplay")=="none",f"expanded Productive composition drifted: {expanded}"); screenshot(sid,"expanded-light")

        sorted_state=execute(sid,"document.querySelector('#sort-name').click();const root=document.querySelector('#scene-filtering'),h=document.querySelector('#sort-name').closest('th'),names=[...root.querySelectorAll('[data-record-row]')].map(x=>x.dataset.name);return [h.getAttribute('aria-sort'),root.dataset.sortKey,root.dataset.sortDirection,names];")
        require(sorted_state[0]=="ascending" and sorted_state[1:3]==["name","ascending"] and sorted_state[3]==["Alpha","Beta","Zulu"],f"sorting failed: {sorted_state}")
        filtered=execute(sid,"const s=document.querySelector('#status-filter');s.value='unknown';s.dispatchEvent(new Event('change',{bubbles:true}));const root=document.querySelector('#scene-filtering');return [root.dataset.visibleRecords,document.querySelector('#filter-count').textContent,[...document.querySelectorAll('#active-filters [data-filter-chip]')].map(x=>x.textContent)];")
        require(filtered[0]=="1" and "1" in filtered[1] and filtered[2]==["Status: unknown"],f"visible filtering failed: {filtered}")
        no_results=execute(sid,"const q=document.querySelector('#table-search');q.value='no-such-fixture';q.dispatchEvent(new Event('input',{bubbles:true}));return [document.querySelector('#scene-filtering').dataset.visibleRecords,document.querySelector('#no-results').hidden,document.querySelector('[data-no-results-query]').textContent];")
        require(no_results==["0",False,"no-such-fixture"],f"no-results context failed: {no_results}")
        cleared=execute(sid,"document.querySelector('#clear-filters').click();const r=document.querySelector('#scene-filtering');return [r.dataset.visibleRecords,r.dataset.sortKey,r.dataset.sortDirection,document.querySelector('#filter-count').textContent];")
        require(cleared[0]=="3" and cleared[1:3]==["name","ascending"] and cleared[3].endswith("0"),f"clear filters reset unrelated sort or failed: {cleared}")

        focus_only=execute(sid,"const row=document.querySelector('#inspect-row-b');row.focus();return [row.dataset.focused,row.dataset.selected,document.querySelector('#inspect-row-a').dataset.selected];")
        require(focus_only==["true","false","false"],f"focus collapsed into selection: {focus_only}")
        single=execute(sid,"document.querySelector('#inspect-a').click();return [document.querySelector('#inspect-row-a').dataset.selected,document.querySelector('#record-inspector [data-inspector-title]').textContent,document.querySelector('#record-inspector [data-selection-count]').textContent];")
        require(single==["true","Gateway North","1 selected"],f"single-selection inspector failed: {single}")
        multi=execute(sid,"document.querySelector('#inspect-b').click();return [document.querySelector('#record-inspector [data-inspector-title]').textContent,document.querySelector('#record-inspector [data-inspector-body]').textContent,document.querySelector('#record-inspector [data-selection-count]').textContent];")
        require(multi[0]=="2 records selected" and "Bulk scope only" in multi[1] and multi[2]=="2 selected",f"multi-selection inspector failed: {multi}")

        states=execute(sid,"return [document.querySelector('#scene-device-manager [data-state=unknown]').textContent,document.querySelector('#scene-service-manager [data-state=stale]').textContent,document.querySelector('#scene-metrics-table [data-state=partial]').textContent,document.querySelector('.glz12-progress-indeterminate').textContent];")
        require("Unknown" in states[0] and "Stale" in states[1] and "Partial" in states[2] and "unknown" in states[3].lower() and "%" not in states[3],f"truthful state presentation failed: {states}")

        log_state=execute(sid,"const root=document.querySelector('#scene-log-viewer'),log=document.querySelector('#log-viewer'),b=document.querySelector('#log-toggle');log.scrollTop=log.scrollHeight;log.dispatchEvent(new Event('scroll'));const live=root.dataset.logLive;log.scrollTop=0;log.dispatchEvent(new Event('scroll'));const paused=[root.dataset.logLive,b.textContent,b.getAttribute('aria-pressed')];b.click();return [live,paused,[root.dataset.logLive,b.textContent,b.getAttribute('aria-pressed')],log.scrollHeight>log.clientHeight];")
        require(log_state[0]=="true" and log_state[1]==["false","Resume live log","true"] and log_state[2]==["true","Pause live log","false"] and log_state[3] is True,f"live-log pause/resume failed: {log_state}")

        viewport(sid,700,960); execute(sid,"document.querySelector('#productive-reference').dataset.glzLayoutClass='expanded';return true;"); time.sleep(.15); local=state(sid); check_page(local,700); require(local.get("networkLocalOverflow") is True,f"wide table lacks local overflow: {local}")

        viewport(sid,390,844); execute(sid,"const r=document.documentElement;r.removeAttribute('dir');r.dataset.glzAppearance='light';r.dataset.glzTouchAssistance='true';document.querySelector('#productive-reference').dataset.glzLayoutClass='compact';return true;"); time.sleep(.15); compact=state(sid); check_page(compact,390,56); require(compact.get("layout")=="compact" and compact.get("filterTableDisplay")=="none" and compact.get("structuredDisplay")!="none",f"compact structured-list transformation failed: {compact}"); screenshot(sid,"compact-assisted")

        execute(sid,"const r=document.documentElement;r.removeAttribute('data-glz-touch-assistance');r.dataset.glzTextScale='200';return true;"); time.sleep(.15); text200=state(sid); check_page(text200,390); screenshot(sid,"compact-text-200")
        execute(sid,"const r=document.documentElement;r.removeAttribute('data-glz-text-scale');r.dataset.glzAppearance='deep-dark';return true;"); time.sleep(.15); dark=state(sid); check_page(dark,390); require(dark.get("appearance")=="deep-dark",f"Deep Dark failed: {dark}"); screenshot(sid,"deep-dark")
        execute(sid,"const r=document.documentElement;r.setAttribute('dir','rtl');r.dataset.glzTransparency='reduced';return true;"); time.sleep(.15); reduced=state(sid); check_page(reduced,390); require(reduced.get("dir")=="rtl" and reduced.get("transparency")=="reduced" and all(x in ("none","") for x in (reduced.get("sceneBackdrop"),reduced.get("inspectorBackdrop"),reduced.get("logBackdrop"))),f"RTL/Reduced Transparency failed: {reduced}")
        media(sid,[{"name":"forced-colors","value":"active"}]); forced=state(sid); check_page(forced,390); screenshot(sid,"rtl-forced-colors")

        print("GLAZE UI V1.2 Productive Interfaces rendered acceptance: PASS")
        return 0
    except (AcceptanceError, AssertionError, KeyError, ValueError, OSError) as error:
        print(f"GLAZE UI V1.2 Productive Interfaces acceptance failed: {error}", file=sys.stderr); return 1
    finally:
        if sid:
            try: request("DELETE",f"/session/{sid}")
            except Exception: pass
        for proc in (driver,http):
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try: proc.wait(timeout=3)
                except subprocess.TimeoutExpired: proc.kill()

if __name__ == "__main__": raise SystemExit(main())

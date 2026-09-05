#!/usr/bin/env python3
"""Exact-head rendered acceptance for bounded GLAZE UI V1.2 Data Visualization Candidate."""
from __future__ import annotations

import base64, json, re, shutil, subprocess, sys, time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
HOST, WEB_PORT, DRIVER_PORT = "127.0.0.1", 8795, 9545
SERVER, DRIVER = f"http://{HOST}:{WEB_PORT}", f"http://{HOST}:{DRIVER_PORT}"
REFERENCE = "reference/v1.2/data-visualization.html"
CONTRACT = ROOT / "contracts/v1.2/data-visualization.candidate.json"
CSS = ROOT / "css/glaze-v1.2-data-visualization.candidate.css"
RUNTIME = ROOT / "js/glaze-v1.2-data-visualization.candidate.mjs"
ENTRYPOINT = ROOT / "css/glaze-v1.2.0-candidate.css"
CATALOG = ROOT / "contracts/components/v1/catalog.json"
SCENES = ["metrics-dashboard","time-series","capacity-storage","network-performance","health-status","timeline-events","comparison-bars","missing-and-forecast"]
PROPOSED = ["GlzMetric","GlzMetricCard","GlzSparkline","GlzLineChart","GlzBarChart","GlzStorageRing","GlzProgressRing","GlzGauge","GlzTimeline","GlzStatusMatrix","GlzNetworkGraph","GlzChartTooltip","GlzChartLegend"]

class AcceptanceError(RuntimeError): pass

def require(ok: bool, message: str) -> None:
    if not ok: raise AcceptanceError(message)

def validate_source() -> None:
    for p in (CONTRACT, CSS, RUNTIME, ENTRYPOINT, CATALOG, ROOT / REFERENCE):
        require(p.is_file(), f"missing {p.relative_to(ROOT)}")
    c = json.loads(CONTRACT.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    require(c.get("version") == "1.2.0-candidate" and c.get("lifecycle") == "candidate" and c.get("consumerEligible") is False, "Data Visualization lifecycle boundary drifted")
    require(c.get("stableBaseline") == "1.1.0", "Data Visualization Stable baseline drifted")
    boundary = c.get("canonicalComponentBoundary", {})
    require(boundary.get("catalogExtensionIntroduced") is False, "Data Visualization must not extend canonical catalog")
    require(boundary.get("proposedExtensionsRemainNonCanonical") == PROPOSED, "proposed visualization extension list drifted")
    require(c.get("referenceScenes") == SCENES, "Data Visualization scene contract drifted")
    rules = c.get("rules", {})
    for key in ("informationBeforeDecoration","denseVisualizationsUseStableNeutralSurfaces","semanticColorKeepsCanonicalMeaning","importantColorHasNonColorCompanion","multiSeriesCannotDependOnColorAlone","baseVisualizationUnderstandableWithoutHover","keyboardInspectionRequiredWhereInteractive","importantChartsRequireAccessibleEquivalent","freshnessVisibleWhenMaterial","missingUnknownUnavailableAndZeroRemainDistinct","estimatedAndForecastValuesRemainDistinctFromMeasured","forecastPresentationCannotImplyCertainty","thresholdsMustComeFromAuthoritativeConfiguration","overallHealthCannotUpgradeMissingDataToPositive","indeterminateProgressCannotFabricatePercentage","trendDirectionDoesNotImplyPositiveOrNegativeWithoutMetricSemantics","comparisonBaselineMustBeIdentified","correlationCannotBePresentedAsCausationWithoutEvidence","realTimePauseDoesNotImplyProducerCollectionStopped","noRuntimeNetworkRequest","noRuntimePersistence","noNewCanonicalComponent","noNewMaterialCalibration"):
        require(rules.get(key) is True, f"Data Visualization rule drifted: {key}")
    require(rules.get("visualizationLayerIntroducesBackdropBlur") is False, "Data Visualization layer may not introduce blur")
    data = c.get("dataAuthorityBoundary", {})
    require(data.get("referenceDataIsFixtureOnly") is True and data.get("runtimeFetchesAuthoritativeData") is False and data.get("runtimePersistsData") is False and data.get("runtimeComputesAuthoritativeHealth") is False and data.get("runtimeInventsThresholds") is False and data.get("runtimeClaimsCausation") is False, "Data Visualization authority boundary drifted")

    flat = [name for names in catalog.get("tiers", {}).values() for name in names]
    require(catalog.get("componentCount") == 32 and len(flat) == 32 and len(set(flat)) == 32, "canonical component catalog drifted")
    require(not any(name in flat for name in PROPOSED), "proposed visualization components leaked into canonical catalog")

    ref = (ROOT / REFERENCE).read_text(encoding="utf-8")
    require(re.findall(r'data-viz-scene="([^"]+)"', ref) == SCENES, "Data Visualization reference scene order drifted")
    for marker in ('fixture data','Updated 2 min ago','solid circle','dashed square','Accessible fixture data equivalent','No producer stream is connected','Overall health: Unknown','does not claim the deployment caused','Baseline: previous fixture hour','Missing gap','Estimated','Forecast','Zero','Unavailable','Fixture threshold:'):
        require(marker in ref, f"Data Visualization reference marker missing: {marker}")
    require(ref.count('role="img"') >= 4 and ref.count('<desc') >= 4, "important visualization SVGs need accessible descriptions")
    require(ref.count('class="glz12-viz-data-table"') >= 3, "important charts need tabular accessible equivalents")
    require('stroke-dasharray' in CSS.read_text(encoding="utf-8") and 'data-pattern="dash"' in ref, "multi-series non-color differentiation missing")
    require('not claim the deployment caused' in ref and 'not certainty' in ref, "causation/forecast certainty boundary missing")

    css = CSS.read_text(encoding="utf-8")
    require("blur(" not in css.lower(), "Data Visualization layer must not introduce blur")
    require("@media (max-width" not in css and "@media (min-width" not in css, "Data Visualization layer must not own viewport-width breakpoints")
    for marker in ('.glz12-viz-scene','.glz12-viz-series-secondary','stroke-dasharray','.glz12-viz-data-table','[data-glz-layout-class="compact"]','data-glz-touch-assistance="true"','--glz12-shell-target-assisted','data-glz-text-scale="200"','data-glz-transparency="reduced"','@media (forced-colors: active)'):
        require(marker in css, f"Data Visualization CSS marker missing: {marker}")

    runtime = RUNTIME.read_text(encoding="utf-8")
    for forbidden in ("fetch(","XMLHttpRequest","WebSocket","localStorage","sessionStorage","indexedDB","navigator.sendBeacon","document.cookie"):
        require(forbidden not in runtime, f"Data Visualization runtime may not transport/persist data: {forbidden}")
    for marker in ("data-viz-point","ArrowRight","data-viz-range","data-viz-live-toggle","does not imply producer collection stopped"):
        require(marker in runtime, f"Data Visualization runtime marker missing: {marker}")

    entry = ENTRYPOINT.read_text(encoding="utf-8")
    productive = '@import url("./glaze-v1.2-productive-interfaces.candidate.css")'
    viz = '@import url("./glaze-v1.2-data-visualization.candidate.css")'
    access = '@import url("./glaze-v1.2-accessibility.candidate.css")'
    require(all(x in entry for x in (productive, viz, access)), "Candidate entrypoint missing Data Visualization import chain")
    require(entry.index(productive) < entry.index(viz) < entry.index(access), "Data Visualization import order drifted")

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
    p = ARTIFACTS / f"glaze-v1.2-data-viz-{name}.png"; p.write_bytes(base64.b64decode(raw)); require(p.stat().st_size > 7000, f"invalid screenshot {p}")

STATE_JS = r"""
const r=document.documentElement,lib=document.querySelector('#viz-reference'),scene=document.querySelector('#viz-time-series'),chart=scene.querySelector('.glz12-viz-chart'),metric=document.querySelector('.glz12-viz-metric');
const nodes=[...document.querySelectorAll('button')].filter(e=>!e.hidden&&getComputedStyle(e).display!=='none'&&e.getClientRects().length);
return {width:innerWidth,scrollWidth:document.documentElement.scrollWidth,layout:lib.dataset.glzLayoutClass,appearance:r.dataset.glzAppearance||'',dir:r.dir||'ltr',transparency:r.dataset.glzTransparency||'',scenes:[...document.querySelectorAll('[data-viz-scene]')].map(e=>e.dataset.vizScene),sceneBackdrop:getComputedStyle(scene).backdropFilter||getComputedStyle(scene).webkitBackdropFilter||'none',chartBackdrop:getComputedStyle(chart).backdropFilter||getComputedStyle(chart).webkitBackdropFilter||'none',metricBackdrop:getComputedStyle(metric).backdropFilter||getComputedStyle(metric).webkitBackdropFilter||'none',metricColumns:getComputedStyle(document.querySelector('.glz12-viz-metric-grid')).gridTemplateColumns.split(/\s+/).filter(Boolean).length,targets:nodes.map(e=>{const b=e.getBoundingClientRect();return{id:e.id||e.textContent.trim().slice(0,36),w:b.width,h:b.height}})};
"""

def state(sid: str) -> dict[str,Any]:
    s=execute(sid,STATE_JS); require(isinstance(s,dict),"could not read Data Visualization state"); return s

def check_page(s: dict[str,Any], width: int, minimum: int = 48) -> None:
    require(abs(int(s.get("width",0))-width)<=1 and int(s.get("scrollWidth",width+2))<=width+1, f"Data Visualization viewport/page overflow failure: {s}")
    require(s.get("scenes")==SCENES, f"Data Visualization scene drifted: {s.get('scenes')}")
    bad=[x for x in s.get("targets",[]) if float(x.get("w",0))<minimum or float(x.get("h",0))<minimum]; require(not bad,f"Data Visualization {minimum}px target floor drifted: {bad}")

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
            if execute(sid,"return document.readyState==='complete' && !!window.GlazeV12DataVisualization"): break
            time.sleep(.1)
        expanded=state(sid); check_page(expanded,1280); require(expanded.get("layout")=="expanded" and expanded.get("metricColumns")==3, f"expanded visualization composition drifted: {expanded}"); require(all(x in ("none","") for x in (expanded.get("sceneBackdrop"),expanded.get("chartBackdrop"),expanded.get("metricBackdrop"))),f"stable visualization surfaces unexpectedly use backdrop blur: {expanded}"); screenshot(sid,"expanded-light")

        point_nav=execute(sid,"const root=document.querySelector('#viz-time-series'),pts=[...root.querySelectorAll('[data-viz-point]')];pts[0].focus();pts[0].dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true}));return [document.activeElement===pts[1],pts.map(p=>p.getAttribute('aria-pressed')),root.dataset.selectedPoint,root.querySelector('[data-viz-inspection]').textContent];")
        require(point_nav[0] is True and point_nav[1]==["false","true","false"] and point_nav[2]=="cpu-0930" and "61 percent" in point_nav[3],f"keyboard point inspection failed: {point_nav}")
        range_state=execute(sid,"const root=document.querySelector('#viz-time-series'),b=[...root.querySelectorAll('[data-viz-range]')].find(x=>x.dataset.vizRange==='24h');b.click();return [root.dataset.range,b.getAttribute('aria-pressed'),root.querySelector('[data-viz-range-status]').textContent];")
        require(range_state[0]=="24h" and range_state[1]=="true" and "24 hours" in range_state[2] and "unchanged" in range_state[2],f"range presentation failed: {range_state}")
        live=execute(sid,"const root=document.querySelector('#viz-network'),b=document.querySelector('#network-live-toggle'),s=root.querySelector('[data-viz-live-status]');b.click();const paused=[root.dataset.visualUpdates,b.getAttribute('aria-pressed'),b.textContent,s.textContent];b.click();return [paused,[root.dataset.visualUpdates,b.getAttribute('aria-pressed'),b.textContent,s.textContent]];")
        require(live[0][0:3]==["paused","true","Resume visual updates"] and "does not imply producer collection stopped" in live[0][3] and live[1][0:3]==["live","false","Pause visual updates"] and "No producer stream is connected" in live[1][3],f"visual pause truth boundary failed: {live}")
        truth=execute(sid,"return [document.querySelector('#viz-health .glz12-viz-state').textContent,document.querySelector('#viz-timeline').textContent,document.querySelector('#viz-comparison').textContent,document.querySelector('#viz-missing').textContent];")
        require("Overall health: Unknown" in truth[0] and "does not claim" in truth[1] and "Baseline: previous fixture hour" in truth[2] and all(x in truth[3] for x in ("Zero","Missing","Unavailable","Unknown","Estimated","Forecast","not certainty","Fixture threshold")),f"visualization truth-state boundary failed: {truth}")

        viewport(sid,390,844); execute(sid,"const r=document.documentElement;r.dataset.glzAppearance='light';r.removeAttribute('dir');r.dataset.glzTouchAssistance='true';document.querySelector('#viz-reference').dataset.glzLayoutClass='compact';return true;"); time.sleep(.15); compact=state(sid); check_page(compact,390,56); require(compact.get("layout")=="compact" and compact.get("metricColumns")==1,f"compact visualization adaptation failed: {compact}"); screenshot(sid,"compact-assisted")
        execute(sid,"const r=document.documentElement;r.removeAttribute('data-glz-touch-assistance');r.dataset.glzTextScale='200';return true;"); time.sleep(.15); text200=state(sid); check_page(text200,390); require(text200.get("metricColumns")==1,f"200% text metric composition failed: {text200}"); screenshot(sid,"compact-text-200")
        execute(sid,"const r=document.documentElement;r.removeAttribute('data-glz-text-scale');r.dataset.glzAppearance='deep-dark';return true;"); time.sleep(.15); dark=state(sid); check_page(dark,390); require(dark.get("appearance")=="deep-dark",f"Deep Dark failed: {dark}"); screenshot(sid,"deep-dark")
        execute(sid,"const r=document.documentElement;r.setAttribute('dir','rtl');r.dataset.glzTransparency='reduced';return true;"); time.sleep(.15); reduced=state(sid); check_page(reduced,390); require(reduced.get("dir")=="rtl" and reduced.get("transparency")=="reduced" and all(x in ("none","") for x in (reduced.get("sceneBackdrop"),reduced.get("chartBackdrop"),reduced.get("metricBackdrop"))),f"RTL/Reduced Transparency failed: {reduced}")
        media(sid,[{"name":"forced-colors","value":"active"}]); forced=state(sid); check_page(forced,390); screenshot(sid,"rtl-forced-colors")

        print("GLAZE UI V1.2 Data Visualization rendered acceptance: PASS")
        return 0
    except (AcceptanceError, AssertionError, KeyError, ValueError, OSError) as error:
        print(f"GLAZE UI V1.2 Data Visualization acceptance failed: {error}", file=sys.stderr); return 1
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

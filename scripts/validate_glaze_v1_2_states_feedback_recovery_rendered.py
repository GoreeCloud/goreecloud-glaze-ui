#!/usr/bin/env python3
"""Exact-head rendered acceptance for bounded GLAZE UI V1.2 States, Feedback, and Recovery Candidate."""
from __future__ import annotations

import base64, json, re, shutil, subprocess, sys, time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
HOST, WEB_PORT, DRIVER_PORT = "127.0.0.1", 8796, 9546
SERVER, DRIVER = f"http://{HOST}:{WEB_PORT}", f"http://{HOST}:{DRIVER_PORT}"
REFERENCE = "reference/v1.2/states-feedback-recovery.html"
CONTRACT = ROOT / "contracts/v1.2/states-feedback-recovery.candidate.json"
CSS = ROOT / "css/glaze-v1.2-states-feedback-recovery.candidate.css"
RUNTIME = ROOT / "js/glaze-v1.2-states-feedback-recovery.candidate.mjs"
ENTRYPOINT = ROOT / "css/glaze-v1.2.0-candidate.css"
CATALOG = ROOT / "contracts/components/v1/catalog.json"
SCENES = ["loading","determinate-progress","indeterminate-progress","success","warning","critical-failure","offline","reconnecting","syncing","partial-success","degraded","stale","unknown","empty","no-results","recovery","recovery-failure","mobile-feedback","deep-dark","reduced-transparency","increased-contrast"]
PROPOSED = ["GlzStatus","GlzStatusBadge","GlzProgress","GlzActivityIndicator","GlzSkeleton","GlzBanner","GlzEmptyState","GlzErrorState","GlzRecoveryState","GlzActivityCenter","GlzSyncState","GlzFreshnessIndicator"]
TRANSITIONS = ["loading,content ready","pending,processing","processing,success","processing,failure","online,offline","offline,connecting,syncing,current","current,stale","error,retry,recovery"]

class AcceptanceError(RuntimeError): pass

def require(ok: bool, message: str) -> None:
    if not ok: raise AcceptanceError(message)

def validate_source() -> None:
    for p in (CONTRACT, CSS, RUNTIME, ENTRYPOINT, CATALOG, ROOT / REFERENCE):
        require(p.is_file(), f"missing {p.relative_to(ROOT)}")
    c = json.loads(CONTRACT.read_text(encoding="utf-8")); catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    require(c.get("version") == "1.2.0-candidate" and c.get("lifecycle") == "candidate" and c.get("consumerEligible") is False, "States lifecycle boundary drifted")
    require(c.get("stableBaseline") == "1.1.0", "States Stable baseline drifted")
    boundary = c.get("canonicalComponentBoundary", {})
    require(boundary.get("catalogExtensionIntroduced") is False and boundary.get("proposedExtensionsRemainNonCanonical") == PROPOSED, "States canonical component boundary drifted")
    require(c.get("referenceScenes") == SCENES, "States reference scene contract drifted")
    require(c.get("transitionAcceptance") == ["loading-to-content","pending-to-processing","processing-to-success","processing-to-failure","online-to-offline","offline-to-connecting-to-syncing-to-current","current-to-stale","error-to-retry-to-recovery"], "States transition contract drifted")
    rules = c.get("rules", {})
    for key in ("truthBeforeDecoration","unknownIsFirstClass","missingEvidenceCannotUpgradeToPositive","successRequiresExplicitCompletionOrAuthoritativePositiveState","warningAndCriticalFailureRemainDistinct","onlineDoesNotImplyHealthySyncedSecureOrProtected","offlineDoesNotImplyFailureDataLossUnhealthyOrUnprotected","pendingQueuedLoadingSyncingPausedFailedAndSuccessRemainDistinct","determinateProgressMustReflectAuthoritativeProgress","indeterminateProgressCannotFabricatePercentage","partialSuccessMustExposeSucceededFailedAndRemainingScope","staleDataMustNotLookCurrent","missingDataMustNotBecomeZero","emptyNoResultsAndLoadFailureRemainDistinct","localFailureShouldRemainLocalWherePossible","retryOnlyWhenRepeatingMayHelp","recoveryCannotDeclareCompleteBeforeAuthoritativeConfirmation","recoveryVerificationRemainsVisibleWhenCompletionDependsOnVerification","syncConflictMustNotSilentlyChooseASide","pendingOfflineChangesMustNotAppearRemotelyCommitted","criticalFailureMustNotDependOnTransientToastOnly","feedbackPersistenceMatchesImportance","importantStateHasNonColorCompanion","noRuntimeNetworkRequest","noRuntimePersistence","noRuntimeProducerTruthComputation","noNewCanonicalComponent","noNewMaterialCalibration"):
        require(rules.get(key) is True, f"States rule drifted: {key}")
    data = c.get("dataAuthorityBoundary", {})
    require(data.get("referenceStateIsFixtureOnly") is True and data.get("runtimeFetchesAuthoritativeState") is False and data.get("runtimePersistsState") is False and data.get("runtimeInfersSecurityPrivacyIdentityHealthSyncOrRecoveryTruth") is False and data.get("producerAcknowledgementEventRequiredForFixtureRecoveryCompletion") is True, "States producer-truth boundary drifted")

    flat = [name for names in catalog.get("tiers", {}).values() for name in names]
    require(catalog.get("componentCount") == 32 and len(flat) == 32 and len(set(flat)) == 32, "canonical component catalog drifted")
    require(not any(name in flat for name in PROPOSED), "proposed state components leaked into canonical catalog")

    ref = (ROOT / REFERENCE).read_text(encoding="utf-8")
    require(re.findall(r'data-state-scene="([^"]+)"', ref) == SCENES, "States reference scene order drifted")
    require(re.findall(r'data-transition-sequence="([^"]+)"', ref) == TRANSITIONS, "States reference transition order drifted")
    for marker in ("All state on this page is fixture-only","Unknown is not healthy","18 completed · 2 failed","Dataset is valid and empty","Offline → Connecting → Syncing → Current","Current → Stale","Pending offline changes are not presented as remotely committed","Recovery failed","must not declare data restored","No percentage is shown","Reduced Transparency","Increased Contrast"):
        require(marker in ref, f"States reference marker missing: {marker}")
    require('aria-live="polite"' in ref and '<progress' in ref, "States accessible progress/announcement semantics missing")

    css = CSS.read_text(encoding="utf-8")
    require("blur(" not in css.lower(), "States layer must not introduce blur")
    require("@media (max-width" not in css and "@media (min-width" not in css, "States layer must not own viewport-width breakpoints")
    for marker in ('.glz12-state-scene','data-state="success"','data-state="warning"','data-state="critical"','data-state="unknown"','data-state="stale"','[data-glz-layout-class="compact"]','data-glz-touch-assistance="true"','--glz12-shell-target-assisted','data-glz-text-scale="200"','data-glz-motion="reduced"','data-glz-transparency="reduced"','data-glz-contrast="increased"','@media (forced-colors: active)'):
        require(marker in css, f"States CSS marker missing: {marker}")

    runtime = RUNTIME.read_text(encoding="utf-8")
    for forbidden in ("fetch(","XMLHttpRequest","WebSocket","localStorage","sessionStorage","indexedDB","navigator.sendBeacon","document.cookie"):
        require(forbidden not in runtime, f"States runtime may not transport/persist state: {forbidden}")
    for marker in ("glz:state-transition-requested","glz:recovery-requested","glz:recovery-producer-state","awaiting producer acknowledgement","detail.status === 'completed' && detail.verified === true"):
        require(marker in runtime, f"States runtime marker missing: {marker}")

    entry = ENTRYPOINT.read_text(encoding="utf-8")
    viz = '@import url("./glaze-v1.2-data-visualization.candidate.css")'; states = '@import url("./glaze-v1.2-states-feedback-recovery.candidate.css")'; access = '@import url("./glaze-v1.2-accessibility.candidate.css")'
    require(all(x in entry for x in (viz, states, access)), "Candidate entrypoint missing States import chain")
    require(entry.index(viz) < entry.index(states) < entry.index(access), "States import order drifted")

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
    raw = request("GET", f"/session/{sid}/screenshot"); require(isinstance(raw,str) and raw, "no screenshot bytes")
    ARTIFACTS.mkdir(exist_ok=True); p = ARTIFACTS / f"glaze-v1.2-states-{name}.png"; p.write_bytes(base64.b64decode(raw)); require(p.stat().st_size > 7000, f"invalid screenshot {p}")

STATE_JS = r"""
const r=document.documentElement,lib=document.querySelector('#state-reference'),scene=document.querySelector('[data-state-scene="loading"]'),box=document.querySelector('.glz12-state-box'),skeleton=document.querySelector('.glz12-skeleton-line');
const nodes=[...document.querySelectorAll('button')].filter(e=>!e.hidden&&getComputedStyle(e).display!=='none'&&e.getClientRects().length);
return {width:innerWidth,scrollWidth:document.documentElement.scrollWidth,layout:lib.dataset.glzLayoutClass,appearance:r.dataset.glzAppearance||'',dir:r.dir||'ltr',transparency:r.dataset.glzTransparency||'',contrast:r.dataset.glzContrast||'',scenes:[...document.querySelectorAll('[data-state-scene]')].map(e=>e.dataset.stateScene),sceneBackdrop:getComputedStyle(scene).backdropFilter||getComputedStyle(scene).webkitBackdropFilter||'none',boxBackdrop:getComputedStyle(box).backdropFilter||getComputedStyle(box).webkitBackdropFilter||'none',skeletonAnimation:getComputedStyle(skeleton).animationName,targets:nodes.map(e=>{const b=e.getBoundingClientRect();return{id:e.textContent.trim().slice(0,44),w:b.width,h:b.height}})};
"""

def state(sid: str) -> dict[str,Any]:
    s=execute(sid,STATE_JS); require(isinstance(s,dict),"could not read States state"); return s

def check_page(s: dict[str,Any], width: int, minimum: int = 48) -> None:
    require(abs(int(s.get("width",0))-width)<=1 and int(s.get("scrollWidth",width+2))<=width+1, f"States viewport/page overflow failure: {s}")
    require(s.get("scenes")==SCENES, f"States scene drifted: {s.get('scenes')}")
    bad=[x for x in s.get("targets",[]) if float(x.get("w",0))<minimum or float(x.get("h",0))<minimum]; require(not bad,f"States {minimum}px target floor drifted: {bad}")

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
            if execute(sid,"return document.readyState==='complete' && !!window.GlazeV12StatesFeedbackRecovery"): break
            time.sleep(.1)
        expanded=state(sid); check_page(expanded,1280); require(expanded.get("layout")=="expanded",f"expanded States layout drifted: {expanded}"); require(expanded.get("sceneBackdrop") in ("none","") and expanded.get("boxBackdrop") in ("none",""),f"States stable surfaces unexpectedly use backdrop blur: {expanded}"); screenshot(sid,"expanded-light")

        transitions=execute(sid,"const run=(sel,n)=>{const s=document.querySelector(sel),b=s.querySelector('[data-transition-advance]');for(let i=0;i<n;i++)b.click();return [s.dataset.currentState,s.querySelector('[data-transition-status]').textContent]};return [run('[data-state-scene=\"loading\"]',1),run('[data-state-scene=\"determinate-progress\"] [data-transition-sequence]',1),run('[data-state-scene=\"success\"] [data-transition-sequence]',1),run('[data-state-scene=\"critical-failure\"] [data-transition-sequence]',1),run('[data-state-scene=\"offline\"]',1),run('[data-state-scene=\"reconnecting\"]',3),run('[data-state-scene=\"stale\"]',1),run('[data-state-scene=\"recovery-failure\"] [data-transition-sequence]',2)];")
        require(transitions==[["content ready","content ready"],["processing","processing"],["success","success"],["failure","failure"],["offline","offline"],["current","current"],["stale","stale"],["recovery","recovery"]],f"truthful fixture transitions failed: {transitions}")

        recovery=execute(sid,"const s=document.querySelector('[data-recovery-root]'),b=s.querySelector('[data-recovery-request]');b.click();const a=[s.dataset.recoveryState,s.querySelector('[data-recovery-status]').textContent,s.querySelector('[data-recovery-verification]').textContent,b.disabled];s.dispatchEvent(new CustomEvent('glz:recovery-producer-state',{detail:{status:'completed',verified:false}}));const u=[s.dataset.recoveryState,s.querySelector('[data-recovery-status]').textContent,s.querySelector('[data-recovery-verification]').textContent];s.dispatchEvent(new CustomEvent('glz:recovery-producer-state',{detail:{status:'completed',verified:true}}));const c=[s.dataset.recoveryState,s.querySelector('[data-recovery-status]').textContent,s.querySelector('[data-recovery-verification]').textContent];return [a,u,c];")
        require(recovery[0][0]=="verifying" and "awaiting producer acknowledgement" in recovery[0][1] and recovery[0][3] is True,f"recovery request gate failed: {recovery}")
        require(recovery[1][0]=="verifying" and "not complete" in recovery[1][1] and "awaiting authoritative confirmation" in recovery[1][2],f"unverified recovery incorrectly completed: {recovery}")
        require(recovery[2][0]=="complete" and "producer acknowledgement" in recovery[2][1] and "confirmed by producer fixture" in recovery[2][2],f"verified recovery acknowledgement failed: {recovery}")

        truth=execute(sid,"return [document.querySelector('[data-state-scene=\"unknown\"]').textContent,document.querySelector('[data-state-scene=\"partial-success\"]').textContent,document.querySelector('[data-state-scene=\"indeterminate-progress\"]').textContent,document.querySelector('[data-state-scene=\"syncing\"]').textContent];")
        require("Unknown is not healthy" in truth[0] and "18 completed · 2 failed" in truth[1] and "%" not in truth[2] and "not presented as remotely committed" in truth[3],f"state truth distinctions failed: {truth}")
        no_results=execute(sid,"const s=document.querySelector('[data-state-scene=\"no-results\"]'),b=s.querySelector('[data-clear-query]');b.click();return [s.querySelector('[data-query-context]').textContent,s.querySelector('[data-query-status]').textContent];")
        require(no_results[0]=="Query: (cleared)" and "does not change producer data" in no_results[1],f"no-results recovery failed: {no_results}")

        execute(sid,"document.querySelector('#state-reference').dataset.glzLayoutClass='compact';document.documentElement.dataset.glzTextScale='200';")
        viewport(sid,360,820); compact=state(sid); check_page(compact,360); require(compact.get("layout")=="compact",f"compact States adaptation drifted: {compact}"); screenshot(sid,"compact-200")

        execute(sid,"document.documentElement.dataset.glzTouchAssistance='true';")
        assisted=state(sid); check_page(assisted,360,56)
        execute(sid,"delete document.documentElement.dataset.glzTouchAssistance;delete document.documentElement.dataset.glzTextScale;document.querySelector('#state-reference').dataset.glzLayoutClass='expanded';document.documentElement.dir='rtl';")
        viewport(sid,1280,960); rtl=state(sid); check_page(rtl,1280); logical=execute(sid,"const b=getComputedStyle(document.querySelector('[data-state-scene=\"stale\"] .glz12-state-box'));return [parseFloat(b.borderRightWidth),parseFloat(b.borderLeftWidth)];"); require(logical[0]>logical[1],f"RTL logical state boundary failed: {logical}")

        execute(sid,"document.documentElement.dataset.glzAppearance='deep-dark';document.documentElement.dataset.glzMotion='reduced';")
        reduced=state(sid); require(reduced.get("skeletonAnimation")=="none",f"Reduced Motion skeleton drifted: {reduced}"); screenshot(sid,"deep-dark-reduced-motion")
        execute(sid,"document.documentElement.dataset.glzTransparency='reduced';")
        transparent=state(sid); require(transparent.get("sceneBackdrop") in ("none","") and transparent.get("boxBackdrop") in ("none",""),f"Reduced Transparency drifted: {transparent}")
        execute(sid,"document.documentElement.dataset.glzContrast='increased';")
        contrast=execute(sid,"const s=getComputedStyle(document.querySelector('[data-state-scene=\"warning\"] .glz12-state-box'));return parseFloat(s.borderTopWidth);"); require(float(contrast)>=3,f"Increased Contrast boundary too weak: {contrast}")

        media(sid,[{"name":"forced-colors","value":"active"}]); forced=execute(sid,"return [matchMedia('(forced-colors: active)').matches,getComputedStyle(document.querySelector('[data-state-scene=\"warning\"]')).forcedColorAdjust];"); require(forced[0] is True and forced[1]=="auto",f"Forced Colors acceptance failed: {forced}"); screenshot(sid,"forced-colors-rtl")
        print("GLAZE UI V1.2 States/Feedback/Recovery Candidate rendered acceptance passed."); return 0
    except AcceptanceError as error:
        print(f"ERROR: {error}",file=sys.stderr); return 1
    finally:
        if sid:
            try: request("DELETE",f"/session/{sid}")
            except Exception: pass
        for proc in (driver,http):
            if proc and proc.poll() is None: proc.terminate()

if __name__ == "__main__": raise SystemExit(main())

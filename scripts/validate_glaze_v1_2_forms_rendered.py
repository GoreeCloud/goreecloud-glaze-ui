#!/usr/bin/env python3
"""Exact-head rendered acceptance for the bounded GLAZE UI V1.2 Forms Candidate."""
from __future__ import annotations

import base64, json, re, shutil, subprocess, sys, time
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
HOST, WEB_PORT, DRIVER_PORT = "127.0.0.1", 8793, 9543
SERVER, DRIVER = f"http://{HOST}:{WEB_PORT}", f"http://{HOST}:{DRIVER_PORT}"
REFERENCE = "reference/v1.2/forms-data-entry.html"
CONTRACT = ROOT / "contracts/v1.2/forms-data-entry.candidate.json"
CSS = ROOT / "css/glaze-v1.2-forms.candidate.css"
RUNTIME = ROOT / "js/glaze-v1.2-forms.candidate.mjs"
ENTRYPOINT = ROOT / "css/glaze-v1.2.0-candidate.css"
CATALOG = ROOT / "contracts/components/v1/catalog.json"
SCENES = ["simple-profile","settings","long-technical-configuration","authentication","password-field","one-time-code","date-time-scheduling","file-selection","validation-failure","destructive-confirmation","multi-step-setup"]
PROPOSED = ["GlzTextArea","GlzNumberField","GlzDateField","GlzTimeField","GlzDateTimeField","GlzPasswordField","GlzFilePicker","GlzFormSection","GlzFieldGroup","GlzValidationMessage","GlzFormActions","GlzStepIndicator"]

class AcceptanceError(RuntimeError): pass

def require(ok: bool, message: str) -> None:
    if not ok: raise AcceptanceError(message)

def validate_source() -> None:
    for p in (CONTRACT, CSS, RUNTIME, ENTRYPOINT, CATALOG, ROOT / REFERENCE):
        require(p.is_file(), f"missing {p.relative_to(ROOT)}")
    c = json.loads(CONTRACT.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    require(c.get("version") == "1.2.0-candidate" and c.get("lifecycle") == "candidate" and c.get("consumerEligible") is False, "Forms lifecycle boundary drifted")
    require(c.get("stableBaseline") == "1.1.0", "Forms Stable baseline drifted")
    boundary = c.get("canonicalComponentBoundary", {})
    require(boundary.get("catalogExtensionIntroduced") is False, "Forms must not extend canonical component catalog")
    require(boundary.get("proposedExtensionsRemainNonCanonical") == PROPOSED, "proposed Forms extension list drifted")
    require(c.get("referenceScenes") == SCENES, "Forms scene contract drifted")
    for key in ("persistentLabelsRequiredForImportantFields","requiredStateCannotDependOnColorAlone","immediateAndDeferredCommitModelsMustBeExplicit","validationMustBeProgrammaticallyAssociated","failedSubmissionMovesFocusToUsefulErrorContext","dirtyStateMustBeVisibleWhenMeaningfulWorkCouldBeLost","authoritativePersistenceRequiredBeforeSavedClaim","duplicateSubmissionGuardRequiredForConsequentialCommit","passwordManagersAndAutofillMustNotBeDisabledForVisualControl","passwordRevealMustNotChangeStoredValue","dragAndDropCannotBeSoleFileSelectionMethod","noRuntimeNetworkRequest","noRuntimeCredentialPersistence","noNewMaterialCalibration","noNewCanonicalComponent"):
        require(c.get("rules", {}).get(key) is True, f"Forms rule drifted: {key}")
    require(c.get("authenticationBoundary", {}).get("realAuthenticationPerformed") is False, "Forms reference may not claim authentication")
    require(c.get("authenticationBoundary", {}).get("credentialsIncludedInCustomEvents") is False, "Forms events may not carry credentials")
    require(c.get("persistenceBoundary", {}).get("runtimePersistsUserData") is False and c.get("persistenceBoundary", {}).get("runtimeCallsRemotePersistence") is False, "Forms persistence boundary drifted")
    require(c.get("persistenceBoundary", {}).get("savedStateRequiresExplicitProducerResultEvent") is True, "Saved requires producer-result event")

    flat = [name for names in catalog.get("tiers", {}).values() for name in names]
    require(catalog.get("componentCount") == 32 and len(flat) == 32 and len(set(flat)) == 32, "canonical component catalog drifted")
    require(not any(name in flat for name in PROPOSED), "proposed Forms components leaked into canonical catalog")

    ref = (ROOT / REFERENCE).read_text(encoding="utf-8")
    require(re.findall(r'data-form-scene="([^"]+)"', ref) == SCENES, "Forms reference scene order drifted")
    for marker in ('data-glz-form-model="deferred"','data-glz-form-model="immediate"','data-glz-form-model="authentication-handoff"','autocomplete="username"','autocomplete="current-password"','autocomplete="one-time-code"','type="date"','type="time"','type="file"','data-glz-confirm-phrase="DELETE WORKSPACE"','Port must be between 1 and 65535.','No authentication attempted'):
        require(marker in ref, f"Forms reference marker missing: {marker}")
    auth = ref[ref.index('id="scene-authentication"'):ref.index('id="scene-password"')]
    require('autocomplete="off"' not in auth and 'autocomplete="username"' in auth and 'autocomplete="current-password"' in auth, "authentication scene must preserve password-manager/autofill semantics")
    require(ref.count('autocomplete="one-time-code"') == 1, "OTP must use one whole-code autofill field")

    css = CSS.read_text(encoding="utf-8")
    require("blur(" not in css.lower(), "Forms layer must not introduce blur")
    require("@media (max-width" not in css and "@media (min-width" not in css, "Forms layer must not own viewport-width breakpoints")
    for marker in ('.glz12-form-surface','.glz12-form-error-summary','[data-glz-layout-class="compact"]','env(safe-area-inset-bottom)','data-glz-text-scale="200"','@media (forced-colors: active)'):
        require(marker in css, f"Forms CSS marker missing: {marker}")

    runtime = RUNTIME.read_text(encoding="utf-8")
    for forbidden in ("fetch(","XMLHttpRequest","WebSocket","localStorage","sessionStorage","new FormData","navigator.sendBeacon"):
        require(forbidden not in runtime, f"Forms runtime may not transport/persist user data: {forbidden}")
    for marker in ("glz:form-submit-requested","glz:form-submission-result","glz:authentication-handoff-requested","glz:destructive-action-requested","glz:immediate-change-requested","data-glz-password-reveal"):
        require(marker in runtime, f"Forms runtime marker missing: {marker}")

    entry = ENTRYPOINT.read_text(encoding="utf-8")
    states, forms, access = '@import url("./glaze-v1.2-interaction-states.candidate.css")', '@import url("./glaze-v1.2-forms.candidate.css")', '@import url("./glaze-v1.2-accessibility.candidate.css")'
    require(all(x in entry for x in (states, forms, access)), "Candidate entrypoint missing Forms/state/accessibility chain")
    require(entry.index(states) < entry.index(forms) < entry.index(access), "Forms import order drifted")

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
    p = ARTIFACTS / f"glaze-v1.2-forms-{name}.png"; p.write_bytes(base64.b64decode(raw)); require(p.stat().st_size > 7000, f"invalid screenshot {p}")

STATE_JS = r"""
const r=document.documentElement,f=document.querySelector('#forms-reference'),pair=document.querySelector('#scene-technical .glz12-form-pair'),surface=document.querySelector('#scene-technical');
const nodes=[...document.querySelectorAll('button,select,input:not([type="checkbox"]):not([type="radio"]),.glz1-switch')].filter(e=>!e.hidden&&getComputedStyle(e).display!=='none');
return {width:innerWidth,scrollWidth:document.documentElement.scrollWidth,layout:f.dataset.glzLayoutClass,dir:r.dir||'ltr',appearance:r.dataset.glzAppearance||'',transparency:r.dataset.glzTransparency||'',scenes:[...document.querySelectorAll('[data-form-scene]')].map(e=>e.dataset.formScene),pairColumns:getComputedStyle(pair).gridTemplateColumns.split(/\s+/).filter(Boolean).length,surfaceBackdrop:getComputedStyle(surface).backdropFilter||getComputedStyle(surface).webkitBackdropFilter||'none',targets:nodes.map(e=>{const b=e.getBoundingClientRect();return{id:e.id||'',w:b.width,h:b.height}})};
"""

def state(sid: str) -> dict[str,Any]:
    s=execute(sid,STATE_JS); require(isinstance(s,dict),"could not read Forms state"); return s

def check(s: dict[str,Any], width: int, minimum: int = 48) -> None:
    require(abs(int(s.get("width",0))-width)<=1 and int(s.get("scrollWidth",width+2))<=width+1, f"Forms viewport/overflow failure: {s}")
    require(s.get("scenes")==SCENES and s.get("surfaceBackdrop")=="none", f"Forms scene/material drifted: {s}")
    bad=[x for x in s.get("targets",[]) if float(x.get("w",0))<minimum or float(x.get("h",0))<minimum]; require(not bad,f"Forms {minimum}px target floor drifted: {bad}")

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
            if execute(sid,"return document.readyState==='complete' && !!window.GlazeV12Forms"): break
            time.sleep(.1)
        expanded=state(sid); check(expanded,1280); require(expanded.get("pairColumns")==2,"expanded Form pair not two columns"); screenshot(sid,"expanded-light")

        dirty=execute(sid,"const f=document.querySelector('#profile-form'),i=document.querySelector('#profile-display-name');i.value='Changed';i.dispatchEvent(new Event('input',{bubbles:true}));return [f.dataset.glzDirty,f.dataset.glzFormState,f.querySelector('[data-glz-form-status]').textContent];")
        require(dirty[0]=="true" and dirty[1]=="unsaved" and "Unsaved" in dirty[2],f"dirty state failed: {dirty}")
        invalid=execute(sid,"const f=document.querySelector('#technical-form');f.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));const s=document.querySelector('#technical-error-summary'),p=document.querySelector('#technical-port');return [s.hidden,document.activeElement&&document.activeElement.id,p.getAttribute('aria-invalid'),f.dataset.glzFormState,document.querySelector('#technical-port-error').textContent];")
        require(invalid[0] is False and invalid[1]=="technical-error-summary" and invalid[2]=="true" and invalid[3]=="invalid" and "65535" in invalid[4],f"validation/focus failed: {invalid}")
        pending=execute(sid,"const f=document.querySelector('#technical-form'),p=document.querySelector('#technical-port');p.value='443';p.dispatchEvent(new Event('input',{bubbles:true}));f.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));f.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));const b=document.querySelector('#technical-submit');return [f.dataset.glzSubmissionPending,f.dataset.glzSubmissionCount,b.disabled,f.dataset.glzFormState];")
        require(pending==["true","1",True,"saving"],f"pending/duplicate guard failed: {pending}")
        saved=execute(sid,"const f=document.querySelector('#technical-form');f.dispatchEvent(new CustomEvent('glz:form-submission-result',{detail:{status:'saved',message:'Saved by producer acknowledgement.'}}));return [f.dataset.glzSubmissionPending,f.dataset.glzDirty,f.dataset.glzFormState,document.querySelector('#technical-status').textContent];")
        require(saved[0]=="false" and saved[1]=="false" and saved[2]=="saved" and "producer" in saved[3],f"producer-result Saved failed: {saved}")
        immediate=execute(sid,"const f=document.querySelector('#settings-form'),c=document.querySelector('#automatic-backups');c.checked=false;c.dispatchEvent(new Event('change',{bubbles:true}));return [f.dataset.glzImmediateCount,f.querySelector('[data-glz-immediate-status]').textContent];")
        require(immediate[0]=="1" and "producer confirmation" in immediate[1],f"immediate model failed: {immediate}")
        reveal=execute(sid,"const i=document.querySelector('#password-reference'),b=document.querySelector('#password-reveal'),v=i.value;b.click();const a=[i.type,i.value,b.getAttribute('aria-pressed')];b.click();return [v,a,i.type,i.value];")
        require(reveal[1]==["text",reveal[0],"true"] and reveal[2]=="password" and reveal[3]==reveal[0],f"password reveal mutated value: {reveal}")
        destructive=execute(sid,"const c=document.querySelector('#scene-destructive'),i=document.querySelector('#destructive-confirm'),b=document.querySelector('#destructive-button');const before=b.disabled;i.value='DELETE WORKSPACE';i.dispatchEvent(new Event('input',{bubbles:true}));const enabled=!b.disabled;b.click();return [before,enabled,c.dataset.glzDestructiveRequestCount];")
        require(destructive==[True,True,"1"],f"destructive confirmation failed: {destructive}")
        auth=execute(sid,"const f=document.querySelector('#authentication-form');let d=null;f.addEventListener('glz:authentication-handoff-requested',e=>d=e.detail,{once:true});f.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));return [d,Object.keys(d||{}).sort(),f.querySelector('[data-glz-form-status]').textContent];")
        require(auth[1]==["formId"] and auth[0].get("formId")=="authentication-form" and "does not authenticate" in auth[2],f"authentication boundary failed: {auth}")
        otp=execute(sid,"const i=document.querySelector('#otp-code');return [document.querySelectorAll('[autocomplete=\"one-time-code\"]').length,i.autocomplete,i.maxLength,i.inputMode,document.querySelector('#file-picker').type];")
        require(otp==[1,"one-time-code",6,"numeric","file"],f"OTP/file-picker semantics failed: {otp}")

        viewport(sid,390,900); execute(sid,"const r=document.documentElement,f=document.querySelector('#forms-reference');f.dataset.glzLayoutClass='compact';r.dataset.glzTextScale='200';return true;"); compact=state(sid); check(compact,390); require(compact.get("pairColumns")==1,"compact 200% Form did not reflow"); screenshot(sid,"compact-text200")
        execute(sid,"document.documentElement.dir='rtl';return true;"); rtl=state(sid); check(rtl,390); require(rtl.get("dir")=="rtl","RTL inactive")
        viewport(sid,1280,960); execute(sid,"const r=document.documentElement,f=document.querySelector('#forms-reference');r.dir='ltr';delete r.dataset.glzTextScale;r.dataset.glzAppearance='deep-dark';r.dataset.glzTransparency='reduced';f.dataset.glzLayoutClass='expanded';return true;"); reduced=state(sid); check(reduced,1280); require(reduced.get("appearance")=="deep-dark" and reduced.get("transparency")=="reduced","Deep Dark/Reduced Transparency inactive"); screenshot(sid,"deep-dark-reduced-transparency")
        execute(sid,"document.documentElement.dataset.glzTouchAssistance='true';return true;"); assisted=state(sid); reps={"technical-port","technical-submit","file-picker","schedule-date","schedule-time"}; bad=[x for x in assisted["targets"] if x["id"] in reps and x["h"]<56]; require(not bad,f"56px assisted Forms targets drifted: {bad}")
        media(sid,[{"name":"forced-colors","value":"active"}]); check(state(sid),1280); media(sid,[])
        print("GLAZE UI V1.2 Forms and Data Entry Candidate: PASS"); return 0
    except Exception as error:
        print(f"GLAZE UI V1.2 Forms and Data Entry acceptance failed: {error}",file=sys.stderr); return 1
    finally:
        if sid:
            try: request("DELETE",f"/session/{sid}")
            except Exception: pass
        for p in (driver,http):
            if p:
                p.terminate()
                try: p.wait(timeout=5)
                except subprocess.TimeoutExpired: p.kill()

if __name__ == "__main__": raise SystemExit(main())

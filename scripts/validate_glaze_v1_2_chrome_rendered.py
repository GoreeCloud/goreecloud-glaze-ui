#!/usr/bin/env python3
"""Bounded rendered-web acceptance for GLAZE UI V1.2 Candidate chrome optics."""
from __future__ import annotations

import base64, json, re, shutil, subprocess, sys, time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
ARTIFACTS=ROOT/"artifacts"
HOST="127.0.0.1"; WEB_PORT=8786; DRIVER_PORT=9536
SERVER=f"http://{HOST}:{WEB_PORT}"; DRIVER=f"http://{HOST}:{DRIVER_PORT}"
REFERENCE="reference/v1.2/chrome-optics.html"
CONTRACT=ROOT/"contracts/v1.2/chrome-optics.candidate.json"
CSS=ROOT/"css/glaze-v1.2-chrome-optics.candidate.css"
ENTRYPOINT=ROOT/"css/glaze-v1.2.0-candidate.css"
COMPONENTS={
    "GlzButton","GlzIconButton","GlzTextField","GlzSelect","GlzSidebar",
    "GlzNavigationRail","GlzDock","GlzToolbar","GlzTooltip","GlzPopover",
    "GlzMenu","GlzSheet","GlzToast","GlzCapsule","GlzSmartRail","GlzSourceChip",
}
SURFACES=("button","iconButton","field","select","sourceChip","sidebar","rail",
          "dock","toolbar","tooltip","popover","menu","sheet","toast","capsule","smartRail")

class AcceptanceError(RuntimeError): pass
def require(ok: bool, msg: str)->None:
    if not ok: raise AcceptanceError(msg)

def validate_source()->None:
    for path in (CONTRACT,CSS,ENTRYPOINT,ROOT/REFERENCE):
        require(path.is_file(),f"missing {path.relative_to(ROOT)}")
    c=json.loads(CONTRACT.read_text())
    require(c.get("version")=="1.2.0-candidate","contract version drifted")
    require(c.get("lifecycle")=="candidate" and c.get("consumerEligible") is False,"Candidate lifecycle boundary drifted")
    require(c.get("stableBaseline")=="1.1.0","Stable baseline drifted")
    require(set(c.get("components",{}))==COMPONENTS,"component coverage drifted")
    rules=c.get("rules",{})
    require(rules.get("nestedBackdropBlurAllowed") is False,"nested blur prohibition drifted")
    require(rules.get("durableReadingSurfacesRemainNonBackdropDependent") is True,"durable-content protection drifted")
    impl=c.get("implementation",{})
    require(impl.get("webLayer")=="css/glaze-v1.2-chrome-optics.candidate.css","web layer binding drifted")
    require(impl.get("reference")==REFERENCE,"reference binding drifted")
    require(impl.get("renderedValidator")=="scripts/validate_glaze_v1_2_chrome_rendered.py","validator binding drifted")
    css=CSS.read_text()
    for marker in ("--glz12-chrome-edge",".glz1-sidebar[data-variant=\"floating\"]",
                   ".glz1-dock",".glz1-popover",".glz1-sheet",".glz1-smart-rail",
                   'data-glz-material-performance="minimal"','data-glz-transparency="reduced"',
                   "@media (forced-colors: active)"):
        require(marker in css,f"CSS marker missing: {marker}")
    e=ENTRYPOINT.read_text()
    names=[
      '@import url("./glaze-v1.2-optical.candidate.css")',
      '@import url("./glaze-v1.2-chrome-optics.candidate.css")',
      '@import url("./glaze-v1.2-legacy-aura-retirement.candidate.css")',
      '@import url("./glaze-v1.2-accessibility.candidate.css")',
    ]
    require(all(x in e for x in names),"Candidate entrypoint missing chrome import chain")
    require([e.index(x) for x in names]==sorted(e.index(x) for x in names),"chrome import order drifted")

def request(method:str,path:str,payload:dict[str,Any]|None=None,timeout:int=30)->Any:
    req=Request(f"{DRIVER}{path}",data=None if payload is None else json.dumps(payload).encode(),
                method=method,headers={"Content-Type":"application/json; charset=utf-8"})
    try:
        with urlopen(req,timeout=timeout) as resp: raw=resp.read()
    except HTTPError as err:
        raise AcceptanceError(f"WebDriver HTTP {err.code}: {err.read().decode(errors='replace')}") from err
    except (URLError,TimeoutError) as err:
        raise AcceptanceError(f"WebDriver request failed: {err}") from err
    if not raw:return None
    value=json.loads(raw.decode()).get("value")
    if isinstance(value,dict) and value.get("error"):
        raise AcceptanceError(f"WebDriver {value.get('error')}: {value.get('message','')}")
    return value

def wait_http(url:str,seconds:float=15)->None:
    end=time.monotonic()+seconds; last=None
    while time.monotonic()<end:
        try:
            with urlopen(url,timeout=1) as r:
                if r.status==200:return
        except Exception as err:last=err
        time.sleep(.15)
    raise AcceptanceError(f"HTTP endpoint not ready: {last}")

def chromedriver()->str:
    for item in (shutil.which("chromedriver"),"/usr/bin/chromedriver","/usr/local/share/chromedriver-linux64/chromedriver"):
        if item and Path(item).is_file():return str(item)
    raise AcceptanceError("chromedriver unavailable")

def wait_driver()->None:
    end=time.monotonic()+15; last=None
    while time.monotonic()<end:
        try:
            s=request("GET","/status")
            if isinstance(s,dict) and s.get("ready"):return
        except Exception as err:last=err
        time.sleep(.2)
    raise AcceptanceError(f"chromedriver not ready: {last}")

def session()->str:
    value=request("POST","/session",{"capabilities":{"alwaysMatch":{"browserName":"chrome","goog:chromeOptions":{"args":[
      "--headless=new","--no-sandbox","--disable-dev-shm-usage","--disable-background-networking",
      "--disable-component-update","--disable-default-apps","--disable-extensions","--disable-sync",
      "--metrics-recording-only","--no-first-run","--window-size=1440,1000"]}}}},timeout=60)
    require(isinstance(value,dict) and isinstance(value.get("sessionId"),str),"Chrome returned no session id")
    return value["sessionId"]

def execute(sid:str,script:str)->Any:
    return request("POST",f"/session/{sid}/execute/sync",{"script":script,"args":[]})
def cdp(sid:str,cmd:str,params:dict[str,Any]|None=None)->Any:
    return request("POST",f"/session/{sid}/goog/cdp/execute",{"cmd":cmd,"params":params or {}})
def viewport(sid:str,w:int,h:int,mobile:bool=False)->None:
    cdp(sid,"Emulation.setDeviceMetricsOverride",{"width":w,"height":h,"deviceScaleFactor":1,"mobile":mobile,"screenWidth":w,"screenHeight":h})
def media(sid:str,features:list[dict[str,str]])->None:
    cdp(sid,"Emulation.setEmulatedMedia",{"media":"screen","features":features})
def navigate(sid:str)->None:
    request("POST",f"/session/{sid}/url",{"url":f"{SERVER}/{REFERENCE}"})
    end=time.monotonic()+15
    while time.monotonic()<end:
        if execute(sid,"return document.readyState")=="complete":return
        time.sleep(.1)
    raise AcceptanceError("reference did not finish loading")
def screenshot(sid:str,name:str)->None:
    encoded=request("GET",f"/session/{sid}/screenshot")
    require(isinstance(encoded,str) and encoded,"no screenshot bytes")
    ARTIFACTS.mkdir(exist_ok=True); path=ARTIFACTS/f"glaze-v1.2-chrome-{name}.png"
    path.write_bytes(base64.b64decode(encoded)); require(path.stat().st_size>8000,f"invalid screenshot {path}")

def blur(value:str)->float:
    if value in ("none",""):return 0
    m=re.search(r"blur\(([\d.]+)px\)",value); require(m is not None,f"expected blur(): {value}")
    return float(m.group(1))

STATE_JS=r'''
const root=document.documentElement, q=s=>document.querySelector(s);
const read=s=>{const e=q(s),c=e&&getComputedStyle(e);return {
  filter:c?(c.backdropFilter||c.webkitBackdropFilter||'none'):'missing',
  background:c&&c.backgroundColor,border:c&&c.borderColor,shadow:c&&c.boxShadow};};
return {
 ready:document.readyState,width:innerWidth,scrollWidth:document.documentElement.scrollWidth,
 version:root.getAttribute('data-glaze-version'),upgrade:root.getAttribute('data-glaze-upgrade'),
 appearance:root.getAttribute('data-glz-appearance'),profile:root.getAttribute('data-glz-material-performance'),
 button:read('.glz1-button[data-variant="glaze"]:not(.nested-proof)'),
 iconButton:read('.glz1-icon-button[data-variant="glaze"]'),
 field:read('.glz1-field-control[data-variant="glaze"]'),select:read('.glz1-select[data-variant="glaze"]'),
 sourceChip:read('.glz1-source-chip[data-material="frosted"]'),sidebar:read('.glz1-sidebar[data-variant="floating"]'),
 rail:read('.glz1-navigation-rail[data-variant="floating"]'),dock:read('.glz1-dock'),
 toolbar:read('.glz1-toolbar[data-variant="floating"]'),tooltip:read('.glz1-tooltip'),
 popover:read('.glz1-popover'),menu:read('.glz1-menu'),sheet:read('.glz1-sheet'),
 toast:read('.glz1-toast'),capsule:read('.glz1-capsule'),smartRail:read('.glz1-smart-rail'),
 nestedButton:read('.glz1-popover .glz1-button[data-variant="glaze"]'),durable:read('.durable-proof'),
 sidebarCurrent:read('.glz1-sidebar-item[aria-current="page"]'),
 railCurrent:read('.glz1-navigation-rail .glz1-rail-item[aria-current="page"]'),
 dockCurrent:read('.glz1-dock-item[aria-current="page"]')
};'''

def state(sid:str)->dict[str,Any]:
    value=execute(sid,STATE_JS); require(isinstance(value,dict),f"could not read chrome state: {value!r}"); return value
def identity(s:dict[str,Any],w:int)->None:
    require(s.get("ready")=="complete" and abs(int(s.get("width",0))-w)<=1,f"page/viewport mismatch: {s}")
    require(int(s.get("scrollWidth",w+2))<=w+1,f"horizontal overflow: {s}")
    require(s.get("version")=="1.1" and s.get("upgrade")=="v1.2-frosted-neutral","Candidate activation boundary missing")
    require(s.get("nestedButton",{}).get("filter")=="none",f"nested frosted control added second blur: {s}")
    require(s.get("durable",{}).get("filter")=="none",f"durable surface gained blur: {s}")
def blurs(s:dict[str,Any])->dict[str,float]:
    return {k:blur(str(s.get(k,{}).get("filter"))) for k in SURFACES}

def full(s:dict[str,Any])->dict[str,float]:
    require(s.get("profile")=="full",f"Full profile inactive: {s}")
    v=blurs(s)
    for k in ("button","iconButton","tooltip"):require(9.5<=v[k]<=10.5,f"{k} not Clear Frost: {s}")
    for k in ("field","select","sourceChip","sidebar","rail"):require(17.5<=v[k]<=18.5,f"{k} not Mist: {s}")
    for k in ("dock","toolbar","popover","menu","toast","capsule","smartRail"):require(27.5<=v[k]<=28.5,f"{k} not Frost: {s}")
    require(43.5<=v["sheet"]<=44.5,f"sheet not Dense Frost: {s}")
    require(v["sheet"]>v["dock"]>v["sidebar"]>v["button"],f"depth/frost hierarchy drifted: {s}")
    for k in ("sidebarCurrent","railCurrent","dockCurrent"):
        cur=s.get(k,{})
        require(cur.get("background") not in (None,"","rgba(0, 0, 0, 0)","transparent"),f"{k} lost visible current state: {s}")
        require(cur.get("border") not in (None,""),f"{k} lost state edge: {s}")
    return v
def set_profile(sid:str,name:str)->dict[str,Any]:
    execute(sid,f"document.documentElement.setAttribute('data-glz-material-performance','{name}');return true;"); return state(sid)
def reduced(s:dict[str,Any],base:dict[str,float])->None:
    require(s.get("profile")=="reduced",f"Reduced inactive: {s}"); v=blurs(s)
    for k in SURFACES:require(0<v[k]<base[k],f"Reduced did not lower {k}: {s}")
    require(v["sheet"]>v["dock"]>v["sidebar"]>v["button"],f"Reduced hierarchy drifted: {s}")
def minimal(s:dict[str,Any])->None:
    require(s.get("profile")=="minimal",f"Minimal inactive: {s}")
    for k in SURFACES:require(s.get(k,{}).get("filter")=="none",f"Minimal must remove {k} blur: {s}")
def reduced_transparency(sid:str)->None:
    execute(sid,"document.documentElement.setAttribute('data-glz-material-performance','full');document.documentElement.setAttribute('data-glz-transparency','reduced');return true;")
    s=state(sid)
    for k in SURFACES:require(s.get(k,{}).get("filter")=="none",f"Reduced Transparency must remove {k}: {s}")
    screenshot(sid,"reduced-transparency"); execute(sid,"document.documentElement.removeAttribute('data-glz-transparency');return true;")
def forced_colors(sid:str)->None:
    media(sid,[{"name":"forced-colors","value":"active"}]); s=state(sid)
    for k in SURFACES:
        require(s.get(k,{}).get("filter")=="none",f"Forced Colors must remove {k} blur: {s}")
        require(s.get(k,{}).get("shadow")=="none",f"Forced Colors must remove {k} shadow: {s}")
    screenshot(sid,"forced-colors"); media(sid,[])
def text_200(sid:str,w:int)->None:
    execute(sid,"document.documentElement.style.fontSize='200%';return true;"); s=state(sid)
    require(int(s.get("scrollWidth",w+2))<=w+1,f"200% text overflow: {s}")
    execute(sid,"document.documentElement.style.fontSize='';return true;")

def main()->int:
    http=driver=None; sid=None
    try:
        validate_source(); ARTIFACTS.mkdir(exist_ok=True)
        http=subprocess.Popen([sys.executable,"-m","http.server",str(WEB_PORT),"--bind",HOST,"--directory",str(ROOT)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,text=True)
        wait_http(f"{SERVER}/{REFERENCE}")
        driver=subprocess.Popen([chromedriver(),f"--port={DRIVER_PORT}","--allowed-ips=127.0.0.1"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,text=True)
        wait_driver(); sid=session(); viewport(sid,1440,1000); media(sid,[]); navigate(sid)
        light=state(sid); identity(light,1440); base=full(light); screenshot(sid,"light-full")
        r=set_profile(sid,"reduced"); identity(r,1440); reduced(r,base); screenshot(sid,"light-reduced")
        m=set_profile(sid,"minimal"); identity(m,1440); minimal(m); screenshot(sid,"light-minimal")
        execute(sid,"document.documentElement.setAttribute('data-glz-material-performance','full');document.documentElement.setAttribute('data-glz-appearance','dark');return true;")
        d=state(sid); identity(d,1440); full(d); screenshot(sid,"dark-full")
        execute(sid,"document.documentElement.setAttribute('data-glz-appearance','deep-dark');return true;")
        dd=state(sid); identity(dd,1440); full(dd); screenshot(sid,"deep-dark-full")
        execute(sid,"document.documentElement.setAttribute('data-glz-appearance','light');return true;")
        reduced_transparency(sid); forced_colors(sid); text_200(sid,1440)
        viewport(sid,390,844,True); navigate(sid); mob=state(sid); identity(mob,390); full(mob); text_200(sid,390); screenshot(sid,"mobile-full")
        print("GLAZE UI V1.2 Frosted Optical chrome rendered web Candidate acceptance: PASS")
        print("Boundary: bounded web Candidate evidence only; V1.1 remains Stable and V1.2 remains non-consumer-eligible.")
        return 0
    except AcceptanceError as err:
        print(f"GLAZE UI V1.2 chrome rendered acceptance failed: {err}",file=sys.stderr); return 1
    finally:
        if sid:
            try:request("DELETE",f"/session/{sid}",timeout=5)
            except Exception:pass
        for proc in (driver,http):
            if proc and proc.poll() is None:
                proc.terminate()
                try:proc.wait(timeout=5)
                except subprocess.TimeoutExpired:proc.kill()
if __name__=="__main__":raise SystemExit(main())

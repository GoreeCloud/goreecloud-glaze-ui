#!/usr/bin/env python3
"""Rendered acceptance for the bounded GLAZE UI V1.2 Motion Candidate."""
from __future__ import annotations
import base64, json, shutil, subprocess, sys, time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT=Path(__file__).resolve().parents[1]; ART=ROOT/"artifacts"
HOST="127.0.0.1"; WEB_PORT=8792; DRIVER_PORT=9542
SERVER=f"http://{HOST}:{WEB_PORT}"; DRIVER=f"http://{HOST}:{DRIVER_PORT}"
REF="reference/v1.2/motion.html"
CONTRACT=ROOT/"contracts/v1.2/motion.candidate.json"; TOKENS=ROOT/"tokens/glaze-v1.2-motion.candidate.json"
CSS=ROOT/"css/glaze-v1.2-motion.candidate.css"; ENTRY=ROOT/"css/glaze-v1.2.0-candidate.css"
WORKFLOW=ROOT/".github/workflows/glaze-v1.2-motion.yml"; EXP_DOC=ROOT/"GLAZE_MOTION.md"; EXP_TOKENS=ROOT/"tokens/glaze-motion.json"
D={"instant":80,"fast":160,"standard":240,"deliberate":360,"spatial":480}
R={"instant":[50,100],"fast":[100,180],"standard":[180,280],"deliberate":[280,420],"spatial":[400,600]}
E={"responsive":"cubic-bezier(0.2, 0, 0, 1)","glide":"cubic-bezier(0.16, 1, 0.3, 1)","settle":"cubic-bezier(0, 0, 0, 1)","direct":"linear"}

class A(RuntimeError): pass
def req(ok,msg):
    if not ok: raise A(msg)
def close(a,b,t=2): return isinstance(a,(int,float)) and abs(float(a)-b)<=t

def source():
    paths=(CONTRACT,TOKENS,CSS,ENTRY,WORKFLOW,ROOT/REF,EXP_DOC,EXP_TOKENS)
    for p in paths: req(p.is_file(),f"missing {p.relative_to(ROOT)}")
    c=json.loads(CONTRACT.read_text()); t=json.loads(TOKENS.read_text()); e=json.loads(EXP_TOKENS.read_text())
    req(c.get("version")=="1.2.0-candidate" and c.get("lifecycle")=="candidate" and c.get("consumerEligible") is False,"Candidate boundary drifted")
    req(c.get("stableBaseline")=="1.1.0" and c.get("status")=="bounded-web-reference-implementation","Stable/bounded boundary drifted")
    p=c["principles"]
    for k in ("respondImmediately","moveWithPurpose","preserveContinuity","settleQuietly","userControlFirst","stateIndependentOfAnimationCompletion","focusMustNotWaitForMotion","connectedIdentityPreferredWhenRelationshipClear","directManipulationTracksInput","userDrivenMotionInterruptible","reducedMotionPreservesSemanticState","reducedMotionPreservesDirectManipulationTracking"): req(p.get(k) is True,f"principle missing {k}")
    for k in ("decorativeContinuousMotionAllowed","routineLinearUiMotionAllowed","excessiveBounceAllowed"): req(p.get(k) is False,f"prohibition drifted {k}")
    for k,v in D.items():
        req(c["durationFamilies"][k]["rangeMs"]==R[k] and c["durationFamilies"][k]["candidateMs"]==v,f"{k} contract duration drifted")
        req(t["durationsMs"][k]==v,f"{k} token drifted")
    req(c["durationFamilies"]["spatial"]["defaultAllowed"] is False,"Spatial became default")
    req(c["easingFamilies"]==E and t["easing"]==E,"easing drifted")
    req(t["profiles"]["full"]["durationsMs"]==D,"full profile drifted")
    req(t["profiles"]["reduced"]["durationsMs"]=={"instant":60,"fast":120,"standard":180,"deliberate":270,"spatial":360},"reduced profile drifted")
    req(all(v==0 for v in t["profiles"]["minimal"]["durationsMs"].values()),"minimal duration drifted")
    x=c["experimentalSubsystemRelationship"]
    req(x["requiredStatus"]=="experimental" and x["wholesalePromotion"] is False and x["runtimeDependencyIntroduced"] is False,"Experimental boundary drifted")
    req(e["glazeMotion"]["status"]=="experimental","Glaze Motion token status was promoted")
    doc=EXP_DOC.read_text(); req("Experimental foundation" in doc and "remains **Experimental**" in doc,"Glaze Motion documentation boundary drifted")
    b=c["representativeBindings"]
    req(b["search"]["sameObjectContinuity"] and b["search"]["focusPreserved"] and b["morphCard"]["sameObjectContinuity"] and b["directManipulation"]["tracksInputImmediately"],"connected/direct bindings drifted")
    imp=c["implementation"]
    expected={"tokens":"tokens/glaze-v1.2-motion.candidate.json","webLayer":"css/glaze-v1.2-motion.candidate.css","webEntrypoint":"css/glaze-v1.2.0-candidate.css","reference":REF,"renderedValidator":"scripts/validate_glaze_v1_2_motion_rendered.py","workflow":".github/workflows/glaze-v1.2-motion.yml"}
    req(imp==expected,"implementation bindings drifted")
    css=CSS.read_text(); low=css.lower()
    for m in ("--glz12-motion-instant: 80ms","--glz12-motion-fast: 160ms","--glz12-motion-standard: 240ms","--glz12-motion-deliberate: 360ms","--glz12-motion-spatial: 480ms",'[data-glz-connected="search"]','[data-glz-connected="card-detail"]','[data-glz-direct-manipulation="true"]',"prefers-reduced-motion: reduce","forced-colors: active"): req(m in css,f"CSS marker missing {m}")
    req("@keyframes" not in low and "infinite" not in low,"autonomous motion introduced")
    req("will-change: auto" in low and "will-change:" not in low.replace("will-change: auto",""),"persistent will-change introduced")
    entry=ENTRY.read_text()
    chain=['@import url("./glaze-v1.2-depth-fallbacks.candidate.css")','@import url("./glaze-v1.2-motion.candidate.css")','@import url("./glaze-v1.2-accessibility.candidate.css")']
    req(all(i in entry for i in chain) and [entry.index(i) for i in chain]==sorted(entry.index(i) for i in chain),"entrypoint order drifted")
    wf=WORKFLOW.read_text(); req("validate_glaze_v1_2_motion_rendered.py" in wf and "github.event.pull_request.head.sha || github.sha" in wf,"workflow binding drifted")

def call(method,path,payload=None,timeout=30):
    q=Request(DRIVER+path,data=None if payload is None else json.dumps(payload).encode(),method=method,headers={"Content-Type":"application/json"})
    try:
        with urlopen(q,timeout=timeout) as r: raw=r.read()
    except (HTTPError,URLError,TimeoutError) as ex: raise A(f"WebDriver request failed: {ex}") from ex
    if not raw:return None
    v=json.loads(raw.decode()).get("value")
    if isinstance(v,dict) and v.get("error"): raise A(f"WebDriver {v.get('error')}: {v.get('message','')}")
    return v
def wait(url):
    end=time.monotonic()+15
    while time.monotonic()<end:
        try:
            with urlopen(url,timeout=1) as r:
                if r.status==200:return
        except Exception: pass
        time.sleep(.15)
    raise A("endpoint not ready")
def driver():
    for p in (shutil.which("chromedriver"),"/usr/bin/chromedriver","/usr/local/share/chromedriver-linux64/chromedriver"):
        if p and Path(p).is_file(): return str(p)
    raise A("chromedriver unavailable")
def execjs(sid,script): return call("POST",f"/session/{sid}/execute/sync",{"script":script,"args":[]})
def cdp(sid,cmd,params): return call("POST",f"/session/{sid}/goog/cdp/execute",{"cmd":cmd,"params":params})
def media(sid,features): cdp(sid,"Emulation.setEmulatedMedia",{"media":"screen","features":features})
def view(sid,w,h): cdp(sid,"Emulation.setDeviceMetricsOverride",{"width":w,"height":h,"deviceScaleFactor":1,"mobile":False,"screenWidth":w,"screenHeight":h})
def shot(sid,name):
    b=call("GET",f"/session/{sid}/screenshot"); req(isinstance(b,str) and b,"no screenshot")
    ART.mkdir(exist_ok=True); p=ART/f"glaze-v1.2-motion-{name}.png"; p.write_bytes(base64.b64decode(b)); req(p.stat().st_size>7000,f"invalid screenshot {p}")

STATE=r"""
const ms=v=>{const a=String(v||'').split(',').map(x=>x.trim()).filter(Boolean).map(x=>x.endsWith('ms')?parseFloat(x):x.endsWith('s')?parseFloat(x)*1000:0);return a.length?Math.max(...a):0};
const st=id=>getComputedStyle(document.getElementById(id)); const root=getComputedStyle(document.documentElement);
const tx=id=>{const t=st(id).transform;return !t||t==='none'?0:new DOMMatrix(t).m41};
const ids=['press-control','selection-indicator','motion-popover','motion-dialog','motion-sheet','search-panel','motion-card','direct-object'];
const anim={}; for(const id of ids)anim[id]=st(id).animationName;
const targets=[...document.querySelectorAll('.glz12-spatial-action')].map(el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);return{id:el.id,w:r.width,h:r.height,visible:s.display!=='none'&&s.visibility!=='hidden'&&parseFloat(s.opacity||'1')>0}});
return{ready:document.readyState,width:innerWidth,scrollWidth:document.documentElement.scrollWidth,
canonical:{instant:ms(root.getPropertyValue('--glz12-motion-instant')),fast:ms(root.getPropertyValue('--glz12-motion-fast')),standard:ms(root.getPropertyValue('--glz12-motion-standard')),deliberate:ms(root.getPropertyValue('--glz12-motion-deliberate')),spatial:ms(root.getPropertyValue('--glz12-motion-spatial'))},
effective:{instant:ms(root.getPropertyValue('--glz12-motion-instant-effective')),fast:ms(root.getPropertyValue('--glz12-motion-fast-effective')),standard:ms(root.getPropertyValue('--glz12-motion-standard-effective')),deliberate:ms(root.getPropertyValue('--glz12-motion-deliberate-effective')),spatial:ms(root.getPropertyValue('--glz12-motion-spatial-effective'))},
dur:{press:ms(st('press-control').transitionDuration),selection:ms(st('selection-indicator').transitionDuration),popover:ms(st('motion-popover').transitionDuration),dialog:ms(st('motion-dialog').transitionDuration),sheet:ms(st('motion-sheet').transitionDuration),searchPanel:ms(st('search-panel').transitionDuration),searchEntry:ms(getComputedStyle(document.querySelector('#motion-search .glz1-search-entry')).transitionDuration),morph:ms(st('motion-card').transitionDuration),direct:ms(st('direct-object').transitionDuration)},
tr:{selectionX:tx('selection-indicator'),popover:st('motion-popover').transform,dialog:st('motion-dialog').transform,sheet:st('motion-sheet').transform,searchPanel:st('search-panel').transform,directX:tx('direct-object')},
state:{popover:document.getElementById('motion-popover').dataset.open,dialog:document.getElementById('motion-dialog').dataset.open,sheet:document.getElementById('motion-sheet').dataset.open,search:document.getElementById('motion-search').dataset.open,morph:document.getElementById('motion-card').getAttribute('aria-expanded'),selected:[...document.querySelectorAll('#selection-track [role="tab"]')].findIndex(x=>x.getAttribute('aria-selected')==='true'),active:document.activeElement&&document.activeElement.id,query:document.getElementById('search-query').value,panelDisplay:st('search-panel').display,panelOpacity:parseFloat(st('search-panel').opacity),morphHeight:document.getElementById('motion-card').getBoundingClientRect().height},anim,targets};
"""
def state(sid):
    v=execjs(sid,STATE); req(isinstance(v,dict),"could not read state"); return v
def visible_targets(s): return [t for t in s["targets"] if t.get("visible")]
def no_overflow(s): req(int(s["scrollWidth"])<=int(s["width"])+1,f"horizontal overflow {s['scrollWidth']}>{s['width']}")
def floors(s,label):
    a=visible_targets(s); req(a,f"{label}: no visible targets"); req(all(float(t["w"])>=48 and float(t["h"])>=48 for t in a),f"{label}: 48px target drifted {a}")
def canonical(s):
    for k,v in D.items(): req(close(s["canonical"][k],v,.5),f"{k} canonical drifted {s['canonical']}")
    req(all(v=="none" for v in s["anim"].values()),f"autonomous animation {s['anim']}"); floors(s,"normal"); no_overflow(s)
def timings(s):
    e={"press":80,"selection":240,"popover":160,"dialog":240,"sheet":360,"searchPanel":360,"searchEntry":360,"morph":360,"direct":0}
    for k,v in e.items(): req(close(s["dur"][k],v),f"{k} duration drifted {s['dur']}")
def open_now(sid,b,s):
    v=execjs(sid,f"const b=document.getElementById('{b}'),s=document.getElementById('{s}');b.click();return{{open:s.dataset.open,expanded:b.getAttribute('aria-expanded')}}")
    req(v=={"open":"true","expanded":"true"},f"{s} state waited for animation {v}")

def main():
    hp=dp=None; sid=None
    try:
        source(); ART.mkdir(exist_ok=True)
        hp=subprocess.Popen([sys.executable,"-m","http.server",str(WEB_PORT),"--bind",HOST,"--directory",str(ROOT)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); wait(SERVER+"/"+REF)
        dp=subprocess.Popen([driver(),f"--port={DRIVER_PORT}","--allowed-ips=127.0.0.1"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); wait(DRIVER+"/status")
        v=call("POST","/session",{"capabilities":{"alwaysMatch":{"browserName":"chrome","goog:chromeOptions":{"args":["--headless=new","--no-sandbox","--disable-dev-shm-usage","--disable-background-networking","--disable-component-update","--disable-extensions","--disable-sync","--metrics-recording-only","--no-first-run","--window-size=1280,1100"]}}}},60); sid=v["sessionId"]
        media(sid,[]); view(sid,1280,1100); call("POST",f"/session/{sid}/url",{"url":SERVER+"/"+REF})
        end=time.monotonic()+15
        while time.monotonic()<end:
            if execjs(sid,"return document.readyState==='complete'&&document.documentElement.dataset.motionReferenceReady==='true'"):break
            time.sleep(.1)
        else: raise A("reference did not load")
        s=state(sid); canonical(s); timings(s); req(s["state"]["selected"]==0,"initial selection drifted")
        n=execjs(sid,"document.getElementById('select-three').click();return [...document.querySelectorAll('#selection-track [role=\"tab\"]')].findIndex(x=>x.getAttribute('aria-selected')==='true')")
        req(n==2,"selection state waited for motion"); time.sleep(.3); req(state(sid)["tr"]["selectionX"]>120,"selection indicator did not move")
        open_now(sid,"popover-toggle","motion-popover");open_now(sid,"dialog-toggle","motion-dialog");open_now(sid,"sheet-toggle","motion-sheet");time.sleep(.4)
        s=state(sid)
        for k in ("popover","dialog","sheet"): req(s["state"][k]=="true" and s["tr"][k]=="none",f"{k} did not settle")
        execjs(sid,"window.__q=document.getElementById('search-query');window.__q.value='continuity';return true")
        q=execjs(sid,"document.getElementById('search-toggle').click();return{open:document.getElementById('motion-search').dataset.open,same:window.__q===document.getElementById('search-query'),value:document.getElementById('search-query').value,active:document.activeElement.id}")
        req(q=={"open":"true","same":True,"value":"continuity","active":"search-query"},f"Search open continuity failed {q}");time.sleep(.4);s=state(sid)
        req(s["state"]["panelDisplay"]=="block" and s["state"]["panelOpacity"]>.98,"Search did not settle");floors(s,"open Search")
        q=execjs(sid,"document.getElementById('search-toggle').click();return{open:document.getElementById('motion-search').dataset.open,same:window.__q===document.getElementById('search-query'),value:document.getElementById('search-query').value,active:document.activeElement.id}")
        req(q=={"open":"false","same":True,"value":"continuity","active":"search-query"},f"Search close continuity failed {q}")
        execjs(sid,"window.__title=document.getElementById('motion-card-title');return true"); h=state(sid)["state"]["morphHeight"]
        m=execjs(sid,"const c=document.getElementById('motion-card');c.click();const a=c.getAttribute('aria-expanded');c.click();const b=c.getAttribute('aria-expanded');c.click();return{a,b,c:c.getAttribute('aria-expanded'),same:window.__title===document.getElementById('motion-card-title')}")
        req(m=={"a":"true","b":"false","c":"true","same":True},f"Morph reversal failed {m}");time.sleep(.4);req(state(sid)["state"]["morphHeight"]>h+40,"MorphCard did not expand")
        x=execjs(sid,"const r=document.getElementById('direct-range');r.value='64';r.dispatchEvent(new Event('input',{bubbles:true}));return new DOMMatrix(getComputedStyle(document.getElementById('direct-object')).transform).m41");req(close(x,64,.5),f"direct tracking failed {x}")
        for a in ("light","dark","deep-dark"):
            execjs(sid,f"document.documentElement.dataset.glzAppearance='{a}';return true");s=state(sid);canonical(s);timings(s);shot(sid,a)
        execjs(sid,"document.documentElement.dataset.glzMaterialPerformance='reduced';return true");s=state(sid)
        for k,v in {"instant":60,"fast":120,"standard":180,"deliberate":270,"spatial":360}.items():req(close(s["effective"][k],v,.5),f"reduced profile drifted {s['effective']}")
        execjs(sid,"document.documentElement.dataset.glzMaterialPerformance='minimal';return true");s=state(sid)
        req(all(close(v,0,.1) for v in s["effective"].values()) and all(close(v,0,.1) for v in s["dur"].values()),f"minimal motion retained {s['effective']} {s['dur']}")
        execjs(sid,"document.documentElement.dataset.glzMaterialPerformance='full';document.documentElement.dataset.mode='reduced-motion';return true");media(sid,[{"name":"prefers-reduced-motion","value":"reduce"}])
        execjs(sid,"document.getElementById('motion-popover').dataset.open='true';document.getElementById('motion-dialog').dataset.open='true';document.getElementById('motion-sheet').dataset.open='true';document.getElementById('motion-search').dataset.open='true';document.getElementById('motion-card').setAttribute('aria-expanded','true');const r=document.getElementById('direct-range');r.value='72';r.dispatchEvent(new Event('input',{bubbles:true}));return true");time.sleep(.1);s=state(sid)
        for k in ("popover","dialog","sheet","searchPanel"):req(s["tr"][k]=="none",f"Reduced Motion travel retained {k}")
        req(s["dur"]["selection"]==0 and s["dur"]["morph"]==0 and all(s["dur"][k]<=80.5 for k in ("popover","dialog","sheet","searchPanel")),"Reduced Motion duration drifted")
        req(close(s["tr"]["directX"],72,.5),"Reduced Motion detached direct manipulation");shot(sid,"reduced-motion")
        execjs(sid,"delete document.documentElement.dataset.mode;return true");media(sid,[{"name":"forced-colors","value":"active"}]);s=state(sid)
        req(all(close(v,0,.1) for v in s["dur"].values()),f"Forced Colors retained transition {s['dur']}");req(all(v=="none" for v in s["anim"].values()),"Forced Colors retained animation");shot(sid,"forced-colors")
        media(sid,[]);view(sid,390,900);execjs(sid,"document.documentElement.dataset.glzAppearance='light';document.documentElement.dataset.glzTextScale='200';document.documentElement.style.fontSize='200%';document.getElementById('motion-search').dataset.open='false';document.getElementById('motion-popover').dataset.open='false';document.getElementById('motion-dialog').dataset.open='false';document.getElementById('motion-sheet').dataset.open='false';return true");s=state(sid);no_overflow(s);floors(s,"compact 200%");shot(sid,"compact-200")
        print("GLAZE UI V1.2 Motion and Connected Transformation rendered validation: PASS");return 0
    except A as e: print(f"GLAZE UI V1.2 Motion and Connected Transformation rendered validation failed: {e}",file=sys.stderr);return 1
    finally:
        if sid:
            try:call("DELETE",f"/session/{sid}")
            except Exception:pass
        for p in (dp,hp):
            if p:
                p.terminate()
                try:p.wait(timeout=3)
                except subprocess.TimeoutExpired:p.kill()
if __name__=="__main__": raise SystemExit(main())

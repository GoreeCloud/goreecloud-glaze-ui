#!/usr/bin/env python3
from __future__ import annotations
import base64,json,shutil,subprocess,sys,time
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'artifacts';HOST='127.0.0.1';WP=8798;DP=9548;SERVER=f'http://{HOST}:{WP}';DRIVER=f'http://{HOST}:{DP}';REF='reference/v1.2/interaction-states.html'
class AcceptanceError(RuntimeError):pass
def require(ok,msg):
    if not ok:raise AcceptanceError(msg)
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def rev():
    try:return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    except Exception:return 'unknown'
def validate_source():
    contract=load(ROOT/'contracts/v1.2/interaction-states.candidate.json');tokens=load(ROOT/'tokens/glaze-v1.2-states.candidate.json');core=load(ROOT/'contracts/v1.2/core-tokens.candidate.json');manifest=load(ROOT/'tokens/glaze-v1.2-core.candidate.json')
    require(contract['lifecycle']=='candidate' and contract['consumerEligible'] is False and contract['stableBaseline']=='1.1.0','state Candidate boundary drifted');require(contract['tokenOwner']=='tokens/glaze-v1.2-states.candidate.json','state owner binding drifted')
    require(list(tokens['states'])==['hover','pressed','selected','disabled','focus','loading','semantic','offline','recovery'],'state token set/order drifted');require(tokens['states']['hover']['overlayOpacity']==0.045 and tokens['states']['pressed']['overlayOpacity']==0.095 and tokens['states']['selected']['overlayOpacity']==0.12,'established V1 state calibration drifted');require(tokens['states']['disabled']['opacity']==0.55,'disabled calibration drifted');require(tokens['states']['focus']['widthPx']==3 and tokens['states']['focus']['offsetPx']==2 and tokens['states']['focus']['increasedContrastWidthPx']==4,'focus calibration drifted')
    state=core['families']['state'];require(state['status']=='candidate-owned' and state['owner']=='tokens/glaze-v1.2-states.candidate.json' and state['pointer']=='/states','core state ownership not established');require(manifest['aliases']['state.interaction']=={'source':'tokens/glaze-v1.2-states.candidate.json','pointer':'/states'},'core state alias drifted');require('state' not in manifest.get('unestablished',{}),'state still incorrectly listed unestablished')
    css=(ROOT/'css/glaze-v1.2-interaction-states.candidate.css').read_text(encoding='utf-8');
    for marker in ('--glz12-state-hover-opacity: .045','--glz12-state-pressed-opacity: .095','--glz12-state-selected-opacity: .12','--glz12-state-disabled-opacity: .55','.glz12-stateful[data-demo-state="focus"]','.glz12-state-busy','@media (prefers-reduced-motion: reduce)','@media (forced-colors: active)'):require(marker in css,f'missing state CSS marker {marker}')
    ref=(ROOT/REF).read_text(encoding='utf-8');
    for marker in ('aria-busy="true"','Loading state includes visible text','Backup verification completed','local data remains safe','Cached files remain available','Three changes are pending upload','Partial:','Awaiting action:'):require(marker in ref,f'missing non-color/truth marker {marker}')
    entry=(ROOT/'css/glaze-v1.2.0-candidate.css').read_text(encoding='utf-8');intel='@import url("./glaze-v1.2-intelligence-components.candidate.css")';states='@import url("./glaze-v1.2-interaction-states.candidate.css")';a11y='@import url("./glaze-v1.2-accessibility.candidate.css")';require(all(x in entry for x in (intel,states,a11y)) and entry.index(intel)<entry.index(states)<entry.index(a11y),'state import order drifted')
def request(method,path,payload=None,timeout=30):
    req=Request(f'{DRIVER}{path}',data=None if payload is None else json.dumps(payload).encode(),method=method,headers={'Content-Type':'application/json; charset=utf-8'})
    try:
        with urlopen(req,timeout=timeout) as r:raw=r.read()
    except HTTPError as e:raise AcceptanceError(f'WebDriver HTTP {e.code}: {e.read().decode(errors="replace")}') from e
    except (URLError,TimeoutError) as e:raise AcceptanceError(f'WebDriver request failed: {e}') from e
    if not raw:return None
    v=json.loads(raw.decode()).get('value')
    if isinstance(v,dict) and v.get('error'):raise AcceptanceError(f"WebDriver {v.get('error')}: {v.get('message','')}")
    return v
def wait_http(url):
    end=time.monotonic()+15
    while time.monotonic()<end:
        try:
            with urlopen(url,timeout=1) as r:
                if r.status==200:return
        except Exception:pass
        time.sleep(.15)
    raise AcceptanceError('HTTP endpoint not ready')
def dp():
    for p in (shutil.which('chromedriver'),'/usr/bin/chromedriver','/usr/local/share/chromedriver-linux64/chromedriver'):
        if p and Path(p).is_file():return str(p)
    raise AcceptanceError('chromedriver unavailable')
def wait_driver():
    end=time.monotonic()+15
    while time.monotonic()<end:
        try:
            if request('GET','/status').get('ready'):return
        except Exception:pass
        time.sleep(.2)
    raise AcceptanceError('chromedriver not ready')
def session():
    v=request('POST','/session',{'capabilities':{'alwaysMatch':{'browserName':'chrome','goog:chromeOptions':{'args':['--headless=new','--no-sandbox','--disable-dev-shm-usage','--disable-background-networking','--disable-component-update','--disable-extensions','--disable-sync','--no-first-run','--window-size=1280,1200']}}}},60);require(isinstance(v,dict) and v.get('sessionId'),'no session id');return v['sessionId']
def execute(sid,s):return request('POST',f'/session/{sid}/execute/sync',{'script':s,'args':[]})
def cdp(sid,cmd,params=None):return request('POST',f'/session/{sid}/goog/cdp/execute',{'cmd':cmd,'params':params or {}})
def shot(sid,name):raw=request('GET',f'/session/{sid}/screenshot');p=ART/name;p.write_bytes(base64.b64decode(raw));return p.name
def run_rendered():
    ART.mkdir(exist_ok=True);http=subprocess.Popen([shutil.which('python3') or sys.executable,'-m','http.server',str(WP),'--bind',HOST],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);drv=subprocess.Popen([dp(),f'--port={DP}','--allowed-ips='],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);sid=None
    try:
        wait_http(f'{SERVER}/{REF}');wait_driver();sid=session();request('POST',f'/session/{sid}/url',{'url':f'{SERVER}/{REF}'});end=time.monotonic()+15
        while time.monotonic()<end:
            if execute(sid,"return document.readyState==='complete'&&window.interactionStatesReady===true"):break
            time.sleep(.1)
        else:raise AcceptanceError('state reference not ready')
        base=execute(sid,"""const q=s=>document.querySelector(s),ps=(s)=>getComputedStyle(q(s),'::after'),c=s=>getComputedStyle(q(s)),b=s=>q(s).getBoundingClientRect();return {appearance:document.documentElement.dataset.glzAppearance,hover:ps('#state-hover').opacity,pressed:ps('#state-pressed').opacity,selected:ps('#state-selected').opacity,disabled:c('#state-disabled').opacity,focusWidth:c('#state-focus').outlineWidth,focusOffset:c('#state-focus').outlineOffset,loadingBusy:q('#state-loading').getAttribute('aria-busy'),height:b('#state-loading').height,success:q('#semantic-success').textContent.trim(),offline:q('#offline-state').textContent.trim(),partial:q('#recovery-partial').textContent.trim()};""");require(base['appearance']=='light','reference default must be light');require(base['hover']=='0.045' and base['pressed']=='0.095' and base['selected']=='0.12','state overlay calibration failed');require(base['disabled']=='0.55','disabled opacity failed');require(base['focusWidth']=='3px' and base['focusOffset']=='2px','focus geometry failed');require(base['loadingBusy']=='true' and base['height']>=48,'loading semantics/target failed');require('Success:' in base['success'] and 'Cached files remain available' in base['offline'] and 'Partial:' in base['partial'],'truth labels missing')
        appearances=execute(sid,"""const q=s=>document.querySelector(s),out={};for(const a of ['light','dark','deep-dark']){document.documentElement.dataset.glzAppearance=a;const s=getComputedStyle(q('#semantic-warning'));out[a]={background:s.backgroundColor,color:s.color,border:s.borderInlineStartColor}}document.documentElement.dataset.glzAppearance='light';return out;""");
        for a in ('light','dark','deep-dark'):require(appearances[a]['background'] not in ('','rgba(0, 0, 0, 0)') and appearances[a]['color'] not in ('','rgba(0, 0, 0, 0)'),f'{a} state rendering failed')
        wide=shot(sid,'glaze-v1.2-interaction-states-wide.png');cdp(sid,'Emulation.setDeviceMetricsOverride',{'width':390,'height':900,'deviceScaleFactor':1,'mobile':False,'screenWidth':390,'screenHeight':900});adaptive=execute(sid,"document.documentElement.dir='rtl';document.documentElement.dataset.glzTextScale='200';const q=s=>document.querySelector(s);return {direction:getComputedStyle(document.body).direction,width:q('#offline-state').getBoundingClientRect().width,viewport:innerWidth,columns:getComputedStyle(q('.glz12-state-scene')).gridTemplateColumns};");require(adaptive['direction']=='rtl' and adaptive['width']<=adaptive['viewport']+1,'compact RTL overflow failed');compact=shot(sid,'glaze-v1.2-interaction-states-compact-rtl.png')
        cdp(sid,'Emulation.setEmulatedMedia',{'media':'screen','features':[{'name':'prefers-reduced-motion','value':'reduce'}]});reduced=execute(sid,"return {anim:getComputedStyle(document.querySelector('.glz12-state-busy'),'::before').animationName,transition:getComputedStyle(document.querySelector('#state-hover'),'::after').transitionDuration}");require(reduced['anim']=='none','reduced motion did not stop busy animation')
        cdp(sid,'Emulation.setEmulatedMedia',{'media':'screen','features':[{'name':'forced-colors','value':'active'}]});forced=execute(sid,"return {active:matchMedia('(forced-colors: active)').matches,focus:getComputedStyle(document.querySelector('#state-focus')).outlineColor}");require(forced['active'] is True,'forced colors emulation failed')
        return {'sourceRevision':rev(),'baseline':base,'appearances':appearances,'adaptive':adaptive,'reducedMotion':reduced,'forcedColors':forced,'screenshots':[wide,compact]}
    finally:
        if sid:
            try:request('DELETE',f'/session/{sid}',timeout=5)
            except Exception:pass
        for p in (drv,http):
            p.terminate()
            try:p.wait(timeout=5)
            except subprocess.TimeoutExpired:p.kill()
def main():
    ART.mkdir(exist_ok=True);p=ART/'glaze-v1.2-interaction-states-evidence.json';e={'sourceRevision':rev(),'status':'started'};p.write_text(json.dumps(e,indent=2)+'\n')
    try:validate_source();e=run_rendered();e['status']='passed';p.write_text(json.dumps(e,indent=2)+'\n');print('GLAZE UI V1.2 interaction-state Candidate acceptance passed');return 0
    except Exception as err:e['status']='failed';e['error']=str(err);p.write_text(json.dumps(e,indent=2)+'\n');print(f'GLAZE UI V1.2 interaction-state Candidate acceptance failed: {err}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())

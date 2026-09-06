#!/usr/bin/env python3
from __future__ import annotations
import base64, json, shutil, subprocess, sys, time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT=Path(__file__).resolve().parents[1]; ART=ROOT/'artifacts'; HOST='127.0.0.1'; WEB_PORT=8797; DRIVER_PORT=9547
SERVER=f'http://{HOST}:{WEB_PORT}'; DRIVER=f'http://{HOST}:{DRIVER_PORT}'; REF='reference/v1.2/intelligence-components.html'
EXPECTED=['GlzAIAction','GlzAISuggestion','GlzAIAnswer','GlzSmartSummary','GlzSourceChip']
class AcceptanceError(RuntimeError): pass
def require(ok,msg):
    if not ok: raise AcceptanceError(msg)
def load(path): return json.loads(path.read_text(encoding='utf-8'))
def rev():
    try:return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    except Exception:return 'unknown'

def validate_source():
    contract=load(ROOT/'contracts/v1.2/intelligence-components.candidate.json'); catalog=load(ROOT/'contracts/components/v1/catalog.json'); materials=load(ROOT/'contracts/v1.2/component-materials.candidate.json')
    require(contract['lifecycle']=='candidate' and contract['consumerEligible'] is False,'Intelligence Candidate boundary drifted')
    require(contract['stableBaseline']=='1.1.0' and contract['tier']=='intelligence','Intelligence lifecycle/tier drifted')
    require(catalog['tiers']['intelligence']==EXPECTED,'canonical Intelligence catalog drifted')
    require([x['id'] for x in contract['components']]==EXPECTED,'Intelligence family set/order drifted')
    require(contract['identityRules']['unrelatedPurpleOrNeonAIIdentityProhibited'] is True,'AI identity restraint missing')
    require(contract['identityRules']['arbitraryColorAsPrimaryDifferentiatorProhibited'] is True,'AI color restraint missing')
    require(contract['identityRules']['semanticMeaningMayDependOnColorAlone'] is False,'AI semantics may not depend on color')
    rules=contract['universalRules']; require(rules['minimumInteractiveTargetPx']==48 and rules['assistedInteractiveTargetPx']==56,'target floors drifted')
    for key in ('durableReadingBackdropDependencyProhibited','consequentialDecisionBackdropDependencyProhibited','keyboardRequired','reducedMotionRequired','reducedTransparencyRequired','increasedContrastRequired','forcedColorsPlatformAuthoritative','textScale200Required','rtlWhereApplicable','noNewRuntimeDependency'): require(rules[key] is True,f'missing rule {key}')
    expected_material={'GlzAIAction':'control-local','GlzAISuggestion':'surface','GlzAIAnswer':'surface','GlzSmartSummary':'surface','GlzSourceChip':'raised'}
    for cid,mat in expected_material.items(): require(materials['components'][cid]['defaultMaterial']==mat,f'{cid} material drifted')
    css=(ROOT/'css/glaze-v1.2-intelligence-components.candidate.css').read_text(encoding='utf-8')
    require('blur(' not in css.lower(),'Intelligence layer must not introduce blur calibration')
    for marker in ('.glz1-ai-action[data-confirming="true"]','.glz1-ai-suggestion[data-dismissed="true"]','.glz12-ai-uncertainty','.glz12-system-truth','.glz1-source-chip:is(button,a,[role="button"])','[data-glz-text-scale="200"]','@media (forced-colors: active)'): require(marker in css,f'missing CSS marker {marker}')
    runtime=(ROOT/'js/glaze-v1.2-intelligence.candidate.mjs').read_text(encoding='utf-8')
    for marker in ('bindV12AIAction','bindV12AISuggestion','bindV12SmartSummary','confirmationRequired','root.hidden = true','toggle.setAttribute("aria-expanded"'): require(marker in runtime,f'missing runtime marker {marker}')
    ref=(ROOT/REF).read_text(encoding='utf-8')
    for marker in ('AI-assisted action','Uses: selected file metadata','Changes state: yes','Confirmation: required','AI suggestion','AI-generated answer','Uncertainty:','Verified system state:','data-source-type="system-event"','Smart summary'): require(marker in ref,f'missing visible semantic marker {marker}')
    entry=(ROOT/'css/glaze-v1.2.0-candidate.css').read_text(encoding='utf-8')
    sig='@import url("./glaze-v1.2-signature-components.candidate.css")'; intel='@import url("./glaze-v1.2-intelligence-components.candidate.css")'; a11y='@import url("./glaze-v1.2-accessibility.candidate.css")'
    require(all(x in entry for x in (sig,intel,a11y)) and entry.index(sig)<entry.index(intel)<entry.index(a11y),'Intelligence import order drifted')
    workflow=(ROOT/'.github/workflows/glaze-v1.2-intelligence-components.yml').read_text(encoding='utf-8')
    require('github.event.pull_request.head.sha || github.sha' in workflow and 'validate_glaze_v1_2_intelligence_components_rendered.py' in workflow,'workflow exact-head/rendered gate missing')

def request(method,path,payload=None,timeout=30):
    req=Request(f'{DRIVER}{path}',data=None if payload is None else json.dumps(payload).encode(),method=method,headers={'Content-Type':'application/json; charset=utf-8'})
    try:
        with urlopen(req,timeout=timeout) as r: raw=r.read()
    except HTTPError as e: raise AcceptanceError(f'WebDriver HTTP {e.code}: {e.read().decode(errors="replace")}') from e
    except (URLError,TimeoutError) as e: raise AcceptanceError(f'WebDriver request failed: {e}') from e
    if not raw:return None
    value=json.loads(raw.decode()).get('value');
    if isinstance(value,dict) and value.get('error'): raise AcceptanceError(f"WebDriver {value.get('error')}: {value.get('message','')}")
    return value

def wait_http(url,seconds=15):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        try:
            with urlopen(url,timeout=1) as r:
                if r.status==200:return
        except Exception:pass
        time.sleep(.15)
    raise AcceptanceError(f'HTTP endpoint not ready: {url}')
def driver_path():
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
    value=request('POST','/session',{'capabilities':{'alwaysMatch':{'browserName':'chrome','goog:chromeOptions':{'args':['--headless=new','--no-sandbox','--disable-dev-shm-usage','--disable-background-networking','--disable-component-update','--disable-extensions','--disable-sync','--no-first-run','--window-size=1280,1200']}}}},60)
    require(isinstance(value,dict) and value.get('sessionId'),'Chrome returned no session id');return value['sessionId']
def execute(sid,script): return request('POST',f'/session/{sid}/execute/sync',{'script':script,'args':[]})
def cdp(sid,cmd,params=None): return request('POST',f'/session/{sid}/goog/cdp/execute',{'cmd':cmd,'params':params or {}})
def viewport(sid,w,h): cdp(sid,'Emulation.setDeviceMetricsOverride',{'width':w,'height':h,'deviceScaleFactor':1,'mobile':False,'screenWidth':w,'screenHeight':h})
def navigate(sid):
    request('POST',f'/session/{sid}/url',{'url':f'{SERVER}/{REF}'});end=time.monotonic()+15
    while time.monotonic()<end:
        if execute(sid,"return document.readyState==='complete' && window.intelligenceReady===true"):return
        time.sleep(.1)
    raise AcceptanceError('Intelligence reference did not become ready')
def screenshot(sid,name):
    raw=request('GET',f'/session/{sid}/screenshot');path=ART/name;path.write_bytes(base64.b64decode(raw));return path.name

def run_rendered():
    ART.mkdir(parents=True,exist_ok=True);http=subprocess.Popen([shutil.which('python3') or sys.executable,'-m','http.server',str(WEB_PORT),'--bind',HOST],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);drv=subprocess.Popen([driver_path(),f'--port={DRIVER_PORT}','--allowed-ips='],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);sid=None
    try:
        wait_http(f'{SERVER}/{REF}');wait_driver();sid=session();navigate(sid)
        baseline=execute(sid,"""const q=s=>document.querySelector(s),b=s=>q(s).getBoundingClientRect(),c=s=>getComputedStyle(q(s));return {appearance:document.documentElement.dataset.glzAppearance,actionHeight:b('#ai-action').height,sourceHeight:b('#source-chip').height,answerBackdrop:c('#ai-answer').backdropFilter||c('#ai-answer').webkitBackdropFilter||'none',label:q('#ai-answer .glz12-ai-label').textContent.trim(),uncertainty:q('.glz12-ai-uncertainty').textContent.trim(),truth:q('.glz12-system-truth').textContent.trim(),sourceType:q('#source-chip').dataset.sourceType};""")
        require(baseline['appearance']=='light','reference must default light');require(baseline['actionHeight']>=48 and baseline['sourceHeight']>=48,'interactive target floor failed');require(baseline['answerBackdrop'] in ('none',''),'AI answer must be solid/readability-first');require('AI-generated answer' in baseline['label'] and 'Uncertainty:' in baseline['uncertainty'] and 'Verified system state:' in baseline['truth'],'AI answer distinctions missing');require(baseline['sourceType']=='system-event','source provenance metadata missing')
        interaction=execute(sid,"""const q=s=>document.querySelector(s);q('#ai-action').click();const a1={state:window.intelligenceControllers.action.getState(),confirming:q('#ai-action').dataset.confirming,status:q('#action-status').textContent};q('#ai-action').click();const a2={state:window.intelligenceControllers.action.getState(),confirming:q('#ai-action').dataset.confirming,status:q('#action-status').textContent};q('#summary-toggle').click();const summary={expanded:q('#summary-toggle').getAttribute('aria-expanded'),data:q('#smart-summary').dataset.expanded,hidden:q('#summary-detail').hidden};q('#suggestion-dismiss').click();const suggestion={hidden:q('#ai-suggestion').hidden,aria:q('#ai-suggestion').getAttribute('aria-hidden'),data:q('#ai-suggestion').dataset.dismissed,status:q('#suggestion-status').textContent};return {a1,a2,summary,suggestion};""")
        require(interaction['a1']['state']['confirming'] is True and interaction['a1']['confirming']=='true' and interaction['a1']['status'].startswith('Confirm'),'first consequential AI activation must confirm');require(interaction['a2']['state']['confirming'] is False and interaction['a2']['confirming']=='false' and interaction['a2']['status'].startswith('Executed'),'second consequential AI activation must execute');require(interaction['summary']=={'expanded':'true','data':'true','hidden':False},'summary ARIA/data/detail synchronization failed');require(interaction['suggestion']['hidden'] is True and interaction['suggestion']['aria']=='true' and interaction['suggestion']['data']=='true','suggestion dismissal failed')
        appearances=execute(sid,"""const q=s=>document.querySelector(s),out={};for(const a of ['light','dark','deep-dark']){document.documentElement.dataset.glzAppearance=a;const s=getComputedStyle(q('#ai-answer'));out[a]={background:s.backgroundColor,color:s.color}}document.documentElement.dataset.glzAppearance='light';return out;""")
        for a in ('light','dark','deep-dark'): require(appearances[a]['background'] not in ('','rgba(0, 0, 0, 0)') and appearances[a]['color'] not in ('','rgba(0, 0, 0, 0)'),f'{a} Intelligence rendering failed')
        wide=screenshot(sid,'glaze-v1.2-intelligence-components-wide.png');viewport(sid,390,900);adaptive=execute(sid,"""document.documentElement.dir='rtl';document.documentElement.dataset.glzTextScale='200';const q=s=>document.querySelector(s);return {direction:getComputedStyle(document.body).direction,width:q('#ai-answer').getBoundingClientRect().width,viewport:innerWidth,headDirection:getComputedStyle(q('.glz12-ai-answer-head')).flexDirection,values:getComputedStyle(q('.glz12-summary-values')).gridTemplateColumns};""");require(adaptive['direction']=='rtl' and adaptive['width']<=adaptive['viewport']+1,'RTL/compact overflow failed');require(adaptive['headDirection']=='column','200%/compact AI answer header adaptation failed');compact=screenshot(sid,'glaze-v1.2-intelligence-components-compact-rtl.png')
        cdp(sid,'Emulation.setEmulatedMedia',{'media':'screen','features':[{'name':'forced-colors','value':'active'}]});forced=execute(sid,"return {active:matchMedia('(forced-colors: active)').matches,answerBackdrop:getComputedStyle(document.querySelector('#ai-answer')).backdropFilter||'none'}");require(forced['active'] is True,'forced colors emulation failed')
        return {'sourceRevision':rev(),'reference':REF,'baseline':baseline,'interactions':interaction,'appearances':appearances,'adaptive':adaptive,'forcedColors':forced,'screenshots':[wide,compact]}
    finally:
        if sid:
            try:request('DELETE',f'/session/{sid}',timeout=5)
            except Exception:pass
        for p in (drv,http):
            p.terminate()
            try:p.wait(timeout=5)
            except subprocess.TimeoutExpired:p.kill()

def main():
    ART.mkdir(parents=True,exist_ok=True);path=ART/'glaze-v1.2-intelligence-components-evidence.json';e={'sourceRevision':rev(),'status':'started'};path.write_text(json.dumps(e,indent=2)+'\n')
    try:validate_source();e=run_rendered();e['status']='passed';path.write_text(json.dumps(e,indent=2)+'\n');print('GLAZE UI V1.2 Intelligence component Candidate acceptance passed');return 0
    except Exception as err:e['status']='failed';e['error']=str(err);path.write_text(json.dumps(e,indent=2)+'\n');print(f'GLAZE UI V1.2 Intelligence component Candidate acceptance failed: {err}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())

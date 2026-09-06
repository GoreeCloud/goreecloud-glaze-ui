#!/usr/bin/env python3
"""Rendered bounded acceptance for the GLAZE UI V1.2 Living Frosted Candidate lab."""
from __future__ import annotations
import base64,json,shutil,subprocess,sys,time
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'artifacts';HOST='127.0.0.1';WP=8812;DP=9562;SERVER=f'http://{HOST}:{WP}';DRIVER=f'http://{HOST}:{DP}';REF='reference/v1.2/living-glaze.html'
class AcceptanceError(RuntimeError):pass
def require(ok,msg):
    if not ok:raise AcceptanceError(msg)
def revision():
    try:return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    except Exception:return 'unknown'
def request(method,path,payload=None,timeout=30):
    req=Request(f'{DRIVER}{path}',data=None if payload is None else json.dumps(payload).encode(),method=method,headers={'Content-Type':'application/json; charset=utf-8'})
    try:
        with urlopen(req,timeout=timeout) as r:raw=r.read()
    except HTTPError as e:raise AcceptanceError(f'WebDriver HTTP {e.code}: {e.read().decode(errors="replace")}') from e
    except (URLError,TimeoutError) as e:raise AcceptanceError(f'WebDriver request failed: {e}') from e
    if not raw:return None
    value=json.loads(raw.decode()).get('value')
    if isinstance(value,dict) and value.get('error'):raise AcceptanceError(f"WebDriver {value.get('error')}: {value.get('message','')}")
    return value
def wait_http(url):
    end=time.monotonic()+15
    while time.monotonic()<end:
        try:
            with urlopen(url,timeout=1) as r:
                if r.status==200:return
        except Exception:pass
        time.sleep(.15)
    raise AcceptanceError('HTTP endpoint not ready')
def driver_path():
    for p in (shutil.which('chromedriver'),'/usr/bin/chromedriver','/usr/local/share/chromedriver-linux64/chromedriver'):
        if p and Path(p).is_file():return str(p)
    raise AcceptanceError('chromedriver unavailable')
def wait_driver():
    end=time.monotonic()+15
    while time.monotonic()<end:
        try:
            status=request('GET','/status')
            if isinstance(status,dict) and status.get('ready'):return
        except Exception:pass
        time.sleep(.2)
    raise AcceptanceError('chromedriver not ready')
def session():
    value=request('POST','/session',{'capabilities':{'alwaysMatch':{'browserName':'chrome','goog:chromeOptions':{'args':['--headless=new','--no-sandbox','--disable-dev-shm-usage','--disable-background-networking','--disable-component-update','--disable-extensions','--disable-sync','--no-first-run','--window-size=1280,1100']}}}},60)
    require(isinstance(value,dict) and value.get('sessionId'),'no session id');return value['sessionId']
def execute(sid,script):return request('POST',f'/session/{sid}/execute/sync',{'script':script,'args':[]})
def cdp(sid,cmd,params=None):return request('POST',f'/session/{sid}/goog/cdp/execute',{'cmd':cmd,'params':params or {}})
def screenshot(sid,name):
    raw=request('GET',f'/session/{sid}/screenshot');path=ART/name;path.write_bytes(base64.b64decode(raw));return path.name

def run():
    ART.mkdir(exist_ok=True)
    subprocess.check_call([sys.executable,str(ROOT/'scripts/validate_glaze_v1_2_living_glaze.py')],cwd=ROOT)
    http=subprocess.Popen([shutil.which('python3') or sys.executable,'-m','http.server',str(WP),'--bind',HOST],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    drv=subprocess.Popen([driver_path(),f'--port={DP}','--allowed-ips='],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);sid=None
    try:
        wait_http(f'{SERVER}/{REF}');wait_driver();sid=session();request('POST',f'/session/{sid}/url',{'url':f'{SERVER}/{REF}'})
        end=time.monotonic()+15
        while time.monotonic()<end:
            if execute(sid,"return document.readyState==='complete'&&window.livingGlazeReady===true"):break
            time.sleep(.1)
        else:raise AcceptanceError('Living Glaze lab not ready')
        baseline=execute(sid,"""const q=s=>document.querySelector(s),b=s=>q(s).getBoundingClientRect(),c=s=>getComputedStyle(q(s));return {appearance:document.documentElement.dataset.glzAppearance,clarity:document.documentElement.dataset.glazeClarity,tier:document.documentElement.dataset.glazeTier,simple:q('#simple').dataset.backdropComplexity,complex:q('#complex').dataset.backdropComplexity,unknown:q('#unknown').dataset.backdropComplexity,pressed:c('#pressed').transform,dragged:c('#dragged').transform,disabledText:q('#disabled').textContent.trim(),capsuleHeight:b('#capsule').height,targetHeights:[...q('#capsule').querySelectorAll('button')].map(x=>x.getBoundingClientRect().height)};""")
        require(baseline['appearance']=='light' and baseline['clarity']=='balanced' and baseline['tier']=='3','default Candidate state drifted')
        require((baseline['simple'],baseline['complex'],baseline['unknown'])==('simple','complex','unknown'),'bounded backdrop complexity markers drifted')
        require('none' not in (baseline['pressed'],baseline['dragged']),'interactive transforms did not render')
        require('Readable content remains intact' in baseline['disabledText'],'disabled content readability marker missing')
        require(all(v>=48 for v in baseline['targetHeights']),'Navigation Capsule target fell below 48px')

        optics=execute(sid,"""document.querySelectorAll('[data-glaze-living]').forEach(e=>e.style.transition='none');const profiles=['clear','balanced','dense'],out={};for(const profile of profiles){document.documentElement.dataset.glazeClarity=profile;void document.body.offsetWidth;const s=getComputedStyle(document.querySelector('#simple')),c=getComputedStyle(document.querySelector('#complex')),u=getComputedStyle(document.querySelector('#unknown'));out[profile]={simple:{background:s.backgroundColor,backdrop:s.backdropFilter,border:s.borderColor},complex:{background:c.backgroundColor,backdrop:c.backdropFilter,border:c.borderColor},unknown:{background:u.backgroundColor,backdrop:u.backdropFilter,border:u.borderColor}}}document.documentElement.dataset.glazeClarity='balanced';return out;""")
        for profile in ('clear','balanced','dense'):
            require(optics[profile]['simple']['background'] != optics[profile]['complex']['background'],f'{profile} backdrop complexity does not alter material density')
            require(optics[profile]['simple']['backdrop'] != optics[profile]['complex']['backdrop'],f'{profile} backdrop complexity does not alter diffusion')
            require('blur(' in optics[profile]['unknown']['backdrop'],f'{profile} deterministic fallback lost Frosted Neutral blur')
        require(len({optics[p]['unknown']['background'] for p in ('clear','balanced','dense')})==3,'Clear/Balanced/Dense do not produce distinct material density')
        require(len({optics[p]['unknown']['backdrop'] for p in ('clear','balanced','dense')})==3,'Clear/Balanced/Dense do not produce distinct diffusion')
        require(len({optics[p]['unknown']['border'] for p in ('clear','balanced','dense')})==3,'Clear/Balanced/Dense do not produce distinct edge treatment')

        clarity=execute(sid,"""const buttons=[...document.querySelectorAll('[data-clarity]')],out={};for(const b of buttons){b.click();out[b.dataset.clarity]=document.documentElement.dataset.glazeClarity}document.documentElement.dataset.glazeClarity='balanced';return out;""")
        require(clarity=={'clear':'clear','balanced':'balanced','dense':'dense'},'clarity controls do not map deterministically')
        wide=screenshot(sid,'glaze-v1.2-living-glaze-wide.png')
        cdp(sid,'Emulation.setDeviceMetricsOverride',{'width':390,'height':900,'deviceScaleFactor':1,'mobile':False,'screenWidth':390,'screenHeight':900})
        compact=execute(sid,"""const n=document.querySelector('#capsule').getBoundingClientRect();return {viewport:innerWidth,left:n.left,right:n.right,width:n.width,targets:[...document.querySelectorAll('#capsule button')].map(x=>x.getBoundingClientRect().height)};""")
        require(compact['left']>=-1 and compact['right']<=compact['viewport']+1,'compact Navigation Capsule overflows viewport')
        require(all(v>=48 for v in compact['targets']),'compact target floor weakened')
        compact_shot=screenshot(sid,'glaze-v1.2-living-glaze-compact.png')

        execute(sid,"document.documentElement.dataset.glzTransparency='reduced'")
        reduced_transparency=execute(sid,"return {backdrop:getComputedStyle(document.querySelector('#complex')).backdropFilter,background:getComputedStyle(document.querySelector('#complex')).backgroundColor};")
        require(reduced_transparency['backdrop']=='none','Reduced Transparency did not remove backdrop dependence')
        execute(sid,"delete document.documentElement.dataset.glzTransparency")

        cdp(sid,'Emulation.setEmulatedMedia',{'media':'screen','features':[{'name':'prefers-reduced-motion','value':'reduce'}]})
        reduced=execute(sid,"return {transition:getComputedStyle(document.querySelector('#simple')).transitionDuration,pressed:getComputedStyle(document.querySelector('#pressed')).transform};")
        require(set(reduced['transition'].split(', '))=={'0s'},'Reduced Motion did not remove Living Glaze transition')
        cdp(sid,'Emulation.setEmulatedMedia',{'media':'screen','features':[{'name':'forced-colors','value':'active'}]})
        forced=execute(sid,"return {active:matchMedia('(forced-colors: active)').matches,backdrop:getComputedStyle(document.querySelector('#complex')).backdropFilter};")
        require(forced['active'] is True,'Forced Colors emulation failed')
        require(forced['backdrop']=='none','Forced Colors did not remove backdrop dependence')
        return {'sourceRevision':revision(),'status':'passed','baseline':baseline,'optics':optics,'clarity':clarity,'compact':compact,'reducedTransparency':reduced_transparency,'reducedMotion':reduced,'forcedColors':forced,'screenshots':[wide,compact_shot]}
    finally:
        if sid:
            try:request('DELETE',f'/session/{sid}',timeout=5)
            except Exception:pass
        for proc in (drv,http):
            proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill()

def main():
    ART.mkdir(exist_ok=True);out=ART/'glaze-v1.2-living-glaze-evidence.json'
    evidence={'sourceRevision':revision(),'status':'started'};out.write_text(json.dumps(evidence,indent=2)+'\n')
    try:evidence=run();out.write_text(json.dumps(evidence,indent=2)+'\n');print('GLAZE UI V1.2 Living Glaze rendered Candidate acceptance passed');return 0
    except Exception as error:evidence['status']='failed';evidence['error']=str(error);out.write_text(json.dumps(evidence,indent=2)+'\n');print(f'GLAZE UI V1.2 Living Glaze rendered Candidate acceptance failed: {error}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())

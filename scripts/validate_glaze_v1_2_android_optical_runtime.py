#!/usr/bin/env python3
"""Bounded Android emulator acceptance for GLAZE UI V1.2 Frosted Optical."""
from __future__ import annotations
import hashlib,json,os,re,subprocess,time,xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/".artifacts/glaze-v1.2-android-optical"
PARITY=ROOT/"contracts/v1.2/native-optical-parity.candidate.json"
PALETTE=ROOT/"reference/v1.2/native/android/app/src/main/java/com/goreecloud/glazeui/reference/v12/OpticalPalette.java"
PACKAGE="com.goreecloud.glazeui.reference.v12"
ACTIVITY=f"{PACKAGE}/.OpticalActivity"
BOUNDS=re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")
EXPECTED={
"frostWhite":"#F4F8FA","crystalWhite":"#FBFDFE","iceBlue":"#DCECF6","glacierBlue":"#8FC4E8",
"clearSkyBlue":"#68AEE0","cloudGray":"#DCE3E8","slateGray":"#7E8D99","coolGraphite":"#151C22",
"deepGraphite":"#0E1419","blueBlack":"#070C11"}
JAVA={"FROST_WHITE":(244,248,250),"CRYSTAL_WHITE":(251,253,254),"ICE_BLUE":(220,236,246),
"GLACIER_BLUE":(143,196,232),"CLEAR_SKY_BLUE":(104,174,224),"CLOUD_GRAY":(220,227,232),
"SLATE_GRAY":(126,141,153),"COOL_GRAPHITE":(21,28,34),"DEEP_GRAPHITE":(14,20,25),"BLUE_BLACK":(7,12,17)}

def run(*a,text=True,check=True): return subprocess.run(a,text=text,check=check,capture_output=True)
def adb(s,*a,text=True,check=True): return run("adb","-s",s,*a,text=text,check=check)
def serial():
    explicit=os.environ.get("ANDROID_SERIAL","").strip()
    if explicit:return explicit
    ds=[l.split()[0] for l in run("adb","devices").stdout.splitlines()[1:] if len(l.split())>1 and l.split()[1]=="device"]
    if len(ds)!=1:raise SystemExit(f"expected one Android target, found {ds}")
    return ds[0]
def revision():
    r=run("git","-C",str(ROOT),"rev-parse","HEAD").stdout.strip();e=os.environ.get("GLAZE_SOURCE_REVISION","").strip()
    if not re.fullmatch(r"[0-9a-f]{40}",r) or (e and e!=r):raise SystemExit(f"revision mismatch checkout={r} expected={e}")
    return r
def source_contract():
    p=json.loads(PARITY.read_text())
    if p.get("opticalPalette")!=EXPECTED or p.get("lifecycle")!="candidate" or p.get("stableBaseline")!="1.1.0":raise SystemExit("native optical parity authority drifted")
    if set(p.get("performanceProfiles",{}))!={"full","reduced","minimal"}:raise SystemExit("profile contract drifted")
    if any(v.get("nativeBackdropBlurClaim") is not False for v in p["performanceProfiles"].values()):raise SystemExit("native blur claim must remain false")
    src=PALETTE.read_text()
    for name,(r,g,b) in JAVA.items():
        if re.search(rf"{name}\s*=\s*Color\.rgb\(\s*{r}\s*,\s*{g}\s*,\s*{b}\s*\)",src) is None:raise SystemExit(f"Android palette role drifted: {name}")
    return {"palette":EXPECTED,"profiles":["full","reduced","minimal"],"nativeBackdropBlurClaim":False}
def density(s):
    raw=adb(s,"shell","wm","density").stdout
    m=re.findall(r"(?:Override|Physical) density:\s*(\d+)",raw)
    return int(m[-1]) if m else int(adb(s,"shell","getprop","ro.sf.lcd_density").stdout.strip())
def dump(s):
    adb(s,"shell","uiautomator","dump","/sdcard/glaze-optical.xml")
    return ET.fromstring(adb(s,"exec-out","cat","/sdcard/glaze-optical.xml").stdout)
def find(root,desc=None,text=None):
    for n in root.iter("node"):
        if desc and n.attrib.get("content-desc")==desc:return n
        if text and (text in n.attrib.get("text","") or text in n.attrib.get("content-desc","")):return n
    return None
def reachable(s,*,desc=None,text=None,tries=12):
    for _ in range(tries):
        n=find(dump(s),desc,text)
        if n is not None:return n
        adb(s,"shell","input","swipe","520","1750","520","650","220");time.sleep(.2)
    raise SystemExit(f"unreachable UI element desc={desc} text={text}")
def bounds(n):
    m=BOUNDS.fullmatch(n.attrib.get("bounds",""))
    if not m:raise SystemExit("invalid bounds")
    return tuple(map(int,m.groups()))
def hdp(n,dpi):
    _,y1,_,y2=bounds(n);return (y2-y1)*160/dpi
def full_target(s,dpi,*,desc,floor,tries=6):
    """Reacquire a target after scrolling until its accessibility bounds are fully visible.

    UIAutomator clips bounds for controls that first enter at a viewport edge. The target
    floor remains unchanged: scrolling only removes viewport clipping and cannot make an
    actually undersized control pass.
    """
    last=0.0
    for _ in range(tries):
        n=find(dump(s),desc=desc)
        if n is None:n=reachable(s,desc=desc)
        last=hdp(n,dpi)
        if last>=floor-1:return n
        _,y1,_,y2=bounds(n);mid=(y1+y2)//2
        if mid>=1200:adb(s,"shell","input","swipe","520","1750","520","950","220")
        else:adb(s,"shell","input","swipe","520","650","520","1450","220")
        time.sleep(.25)
    raise SystemExit(f"{desc} target below floor after viewport re-centering: measured={last:.1f}dp required={floor}dp")
def tap(s,n):
    x1,y1,x2,y2=bounds(n)
    adb(s,"shell","input","tap",str((x1+x2)//2),str((y1+y2)//2));time.sleep(.25)
def launch(s,a,p,reduced=False,touch=False,font=1.0):
    adb(s,"shell","settings","put","system","font_scale",str(font));adb(s,"shell","am","force-stop",PACKAGE)
    args=["shell","am","start","-W","-n",ACTIVITY,"--es","appearance",a,"--es","performanceProfile",p]
    if reduced:args+=["--ez","reducedTransparency","true"]
    if touch:args+=["--ez","touchAssistance","true"]
    if "Status: ok" not in adb(s,*args).stdout:raise SystemExit("OpticalActivity launch failed")
    time.sleep(.6)
def shot(s,name):
    p=OUT/name;data=adb(s,"exec-out","screencap","-p",text=False).stdout;p.write_bytes(data)
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):raise SystemExit("invalid screenshot")
    return name,hashlib.sha256(data).hexdigest()
def case(s,dpi,cid,a,p,reduced=False,touch=False,font=1.0):
    launch(s,a,p,reduced,touch,font)
    for marker in ("Frost White is the material.","Primary material: Frost White","Primary atmosphere: Ice Blue",f"Performance · {p.title()}"):
        reachable(s,text=marker)
    if reduced or p=="minimal":reachable(s,text="Material · Opaque Frost")
    floor=56 if touch else 48
    search=full_target(s,dpi,desc="Universal Search Clear Frost",floor=floor)
    wifi=full_target(s,dpi,desc="Wi-Fi active Ice atmosphere",floor=76)
    action=full_target(s,dpi,desc="Primary action",floor=floor)
    tap(s,action);reachable(s,desc="Action state Complete")
    name,digest=shot(s,f"android-v1.2-{cid}.png")
    return {"id":cid,"appearance":a,"performanceProfile":p,"reducedTransparency":reduced,"touchAssistance":touch,"fontScale":font,"screenshot":name,"sha256":digest,
      "targetFloorsDp":{"search":floor,"quickSetting":76,"primaryAction":floor}}
def main():
    OUT.mkdir(parents=True,exist_ok=True);contract=source_contract();rev=revision();s=serial();dpi=density(s)
    try:
        cases=[case(s,dpi,"light-full","light","full"),
               case(s,dpi,"dark-reduced-transparency","dark","reduced",True),
               case(s,dpi,"deep-dark-minimal-large-text-touch","deep-dark","minimal",False,True,2.0)]
    finally:adb(s,"shell","settings","put","system","font_scale","1.0",check=False)
    evidence={"schemaVersion":1,"product":"GLAZE UI V1.2 Frosted Optical","lifecycle":"Candidate native evidence","sourceRevision":rev,
      "platform":"Android handheld emulator","sourceContract":contract,"cases":cases,
      "boundaries":["not OEM compositor blur fidelity","not physical-device qualification","not TalkBack certification","not production acceptance","not RC or Stable promotion"]}
    (OUT/"android-optical-evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2));print("GLAZE UI V1.2 Frosted Optical Android bounded emulator acceptance: PASS")
if __name__=="__main__":main()

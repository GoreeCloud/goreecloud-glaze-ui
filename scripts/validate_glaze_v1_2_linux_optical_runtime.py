#!/usr/bin/env python3
"""Bounded GTK4/Xvfb acceptance for GLAZE UI V1.2 Frosted Optical."""
from __future__ import annotations
import hashlib,json,os,re,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/"reference/v1.2/native/linux-gtk/optical_app.py"
CSS=ROOT/"reference/v1.2/native/linux-gtk/glaze-v1.2-linux-optical.css"
PARITY=ROOT/"contracts/v1.2/native-optical-parity.candidate.json"
OUT=ROOT/".artifacts/glaze-v1.2-linux-optical"
EXPECTED={"frostWhite":"#F4F8FA","crystalWhite":"#FBFDFE","iceBlue":"#DCECF6","glacierBlue":"#8FC4E8",
"clearSkyBlue":"#68AEE0","cloudGray":"#DCE3E8","slateGray":"#7E8D99","coolGraphite":"#151C22",
"deepGraphite":"#0E1419","blueBlack":"#070C11"}

def run(*a,check=True,env=None):return subprocess.run(a,check=check,text=True,capture_output=True,env=env)
def revision():
    r=run("git","-C",str(ROOT),"rev-parse","HEAD").stdout.strip();e=os.environ.get("GLAZE_SOURCE_REVISION","").strip()
    if not re.fullmatch(r"[0-9a-f]{40}",r) or (e and e!=r):raise SystemExit(f"revision mismatch checkout={r} expected={e}")
    return r
def source_contract():
    p=json.loads(PARITY.read_text());css=CSS.read_text();app=APP.read_text()
    if p.get("opticalPalette")!=EXPECTED or p.get("lifecycle")!="candidate" or p.get("stableBaseline")!="1.1.0":raise SystemExit("native optical parity authority drifted")
    if set(p.get("performanceProfiles",{}))!={"full","reduced","minimal"}:raise SystemExit("profile contract drifted")
    if any(v.get("nativeBackdropBlurClaim") is not False for v in p["performanceProfiles"].values()):raise SystemExit("native blur claim must remain false")
    for marker in ("Frost White is the material.","White behaves as light. Ice Blue behaves as atmosphere.","Primary material: Frost White","Primary atmosphere: Ice Blue","--performance-profile","nativeBackdropBlurClaim"):
        if marker not in app:raise SystemExit(f"GTK optical app missing {marker}")
    for rgb in ("rgb(244,248,250)","rgb(220,236,246)","rgb(143,196,232)","rgb(21,28,34)","rgb(14,20,25)","rgb(7,12,17)"):
        if rgb not in css:raise SystemExit(f"GTK optical CSS missing {rgb}")
    for legacy in ("rgb(15,107,111)","rgb(28,138,141)","rgb(143,214,210)"):
        if legacy in css:raise SystemExit(f"legacy teal leaked into GTK optical CSS: {legacy}")
    return {"palette":EXPECTED,"profiles":["full","reduced","minimal"],"nativeBackdropBlurClaim":False}
def wait(path,proc):
    end=time.monotonic()+15
    while time.monotonic()<end:
        if path.exists() and path.stat().st_size:return json.loads(path.read_text())
        if proc.poll() is not None:
            out,err=proc.communicate();raise SystemExit(f"GTK exited early {proc.returncode}\n{out}\n{err}")
        time.sleep(.1)
    proc.terminate();raise SystemExit("timed out waiting for GTK evidence")
def screenshot(path,env):
    r=run("import","-window","root",str(path),check=False,env=env)
    if r.returncode:raise SystemExit(r.stderr)
    data=path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):raise SystemExit("invalid screenshot")
    return hashlib.sha256(data).hexdigest()
def case(cid,args,profile,minimum,env):
    d=OUT/cid;d.mkdir(parents=True,exist_ok=True);e=d/"runtime.json";e.unlink(missing_ok=True)
    cmd=[sys.executable,str(APP),*args,"--evidence-file",str(e),"--auto-interact"]
    proc=subprocess.Popen(cmd,cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        data=wait(e,proc)
        if not data.get("ready") or data.get("product")!="GLAZE UI V1.2 Frosted Optical" or data.get("lifecycle")!="Candidate native evidence":raise SystemExit(f"{cid} runtime identity drifted")
        if data.get("performanceProfile")!=profile or data.get("nativeBackdropBlurClaim") is not False:raise SystemExit(f"{cid} profile/blur boundary drifted")
        if data.get("opticalRoles")!={"primaryMaterial":"Frost White","primaryAtmosphere":"Ice Blue"}:raise SystemExit(f"{cid} optical roles drifted")
        if data.get("interactionState")!="Action: Complete":raise SystemExit(f"{cid} interaction failed")
        t=data["targets"]
        if int(t["action"])<minimum or int(t["search"])<minimum or any(int(v)<76 for v in t["tiles"]):raise SystemExit(f"{cid} target floor failed: {t}")
        shot=OUT/f"linux-v1.2-{cid}.png";digest=screenshot(shot,env)
        return {"id":cid,"appearance":data["appearance"],"performanceProfile":profile,"targets":t,"screenshot":shot.name,"sha256":digest}
    finally:
        if proc.poll() is None:proc.terminate()
def main():
    OUT.mkdir(parents=True,exist_ok=True);contract=source_contract();rev=revision();env=os.environ.copy();env.setdefault("GDK_BACKEND","x11")
    if not env.get("DISPLAY"):raise SystemExit("DISPLAY required")
    cases=[case("light-full",["--appearance","light","--performance-profile","full"],"full",48,env),
      case("dark-reduced-transparency",["--appearance","dark","--performance-profile","reduced","--reduced-transparency"],"reduced",48,env),
      case("deep-dark-minimal-large-text-touch",["--appearance","deep-dark","--performance-profile","minimal","--large-text","--touch-assistance"],"minimal",56,env)]
    evidence={"schemaVersion":1,"product":"GLAZE UI V1.2 Frosted Optical","lifecycle":"Candidate native evidence","sourceRevision":rev,
      "platform":"Linux GTK4 under Xvfb","sourceContract":contract,"cases":cases,
      "boundaries":["not Wayland compositor blur fidelity","not physical display/GPU qualification","not assistive-technology certification","not production acceptance","not RC or Stable promotion"]}
    (OUT/"linux-optical-evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2));print("GLAZE UI V1.2 Frosted Optical Linux GTK4 bounded acceptance: PASS")
if __name__=="__main__":main()

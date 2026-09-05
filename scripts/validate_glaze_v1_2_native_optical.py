#!/usr/bin/env python3
"""Fail closed on bounded V1.2 native Frosted Optical source drift."""
from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXPECTED={"frostWhite":"#F4F8FA","crystalWhite":"#FBFDFE","iceBlue":"#DCECF6","glacierBlue":"#8FC4E8",
"clearSkyBlue":"#68AEE0","cloudGray":"#DCE3E8","slateGray":"#7E8D99","coolGraphite":"#151C22",
"deepGraphite":"#0E1419","blueBlack":"#070C11"}
def req(c,m):
    if not c:raise SystemExit("GLAZE UI V1.2 native optical source validation failed: "+m)
def text(p):
    q=ROOT/p;req(q.is_file(),"missing "+p);return q.read_text()
def main():
    req(text("VERSION").strip()=="1.1.0","VERSION must remain 1.1.0")
    life=json.loads(text("registry/lifecycle.json"))
    req(life.get("currentStable")=="1.1.0" and life.get("currentOfficial")=="1.1.0","Stable authority moved")
    req(life.get("activeCandidate")=="1.2.0-candidate","active Candidate drifted")
    optical=json.loads(text("tokens/glaze-v1.2-optical-foundation.candidate.json"))
    parity=json.loads(text("contracts/v1.2/native-optical-parity.candidate.json"))
    req(optical.get("opticalPalette")==EXPECTED and parity.get("opticalPalette")==EXPECTED,"optical palette mismatch")
    req(parity.get("lifecycle")=="candidate" and parity.get("stableBaseline")=="1.1.0","native parity lifecycle drifted")
    req(parity.get("status")=="bounded-reference-implementation","native parity status drifted")
    req(parity.get("authority")=="tokens/glaze-v1.2-optical-foundation.candidate.json","native parity authority drifted")
    req(list(parity.get("frostLevels",{}))==["clear","mist","frost","dense-frost","opaque-frost"],"frost order drifted")
    req(set(parity.get("performanceProfiles",{}))=={"full","reduced","minimal"},"profile set drifted")
    req(all(v.get("nativeBackdropBlurClaim") is False for v in parity["performanceProfiles"].values()),"native blur boundary drifted")
    req([x.get("id") for x in parity.get("requiredRuntimeCases",[])]==["light-full","dark-reduced-transparency","deep-dark-minimal-large-text-touch"],"runtime case matrix drifted")
    req("native-optical-parity" in optical.get("evidenceBoundary",{}).get("notEstablished",[]),"full native parity must remain unestablished")

    palette=text("reference/v1.2/native/android/app/src/main/java/com/goreecloud/glazeui/reference/v12/OpticalPalette.java")
    for name,(r,g,b) in {"FROST_WHITE":(244,248,250),"CRYSTAL_WHITE":(251,253,254),"ICE_BLUE":(220,236,246),"GLACIER_BLUE":(143,196,232),
    "CLEAR_SKY_BLUE":(104,174,224),"CLOUD_GRAY":(220,227,232),"SLATE_GRAY":(126,141,153),"COOL_GRAPHITE":(21,28,34),"DEEP_GRAPHITE":(14,20,25),"BLUE_BLACK":(7,12,17)}.items():
        req(re.search(rf"{name}\s*=\s*Color\.rgb\(\s*{r}\s*,\s*{g}\s*,\s*{b}\s*\)",palette) is not None,"Android palette "+name+" drifted")
    android=text("reference/v1.2/native/android/app/src/main/java/com/goreecloud/glazeui/reference/v12/OpticalActivity.java")
    for m in ("Frost White is the material.","White behaves as light. Ice Blue behaves as atmosphere.","Primary material: Frost White","Primary atmosphere: Ice Blue","Universal Search · Clear Frost","Quick Settings · Dense Frost","OPAQUE FROST","performanceProfile"):
        req(m in android,"Android optical reference missing "+m)
    req(".OpticalActivity" in text("reference/v1.2/native/android/app/src/main/AndroidManifest.xml"),"OpticalActivity manifest binding missing")

    app=text("reference/v1.2/native/linux-gtk/optical_app.py");css=text("reference/v1.2/native/linux-gtk/glaze-v1.2-linux-optical.css")
    for m in ("Frost White is the material.","White behaves as light. Ice Blue behaves as atmosphere.","Primary material: Frost White","Primary atmosphere: Ice Blue","--performance-profile","nativeBackdropBlurClaim"):
        req(m in app,"Linux optical reference missing "+m)
    for rgb in ("rgb(244,248,250)","rgb(220,236,246)","rgb(143,196,232)","rgb(21,28,34)","rgb(14,20,25)","rgb(7,12,17)"):
        req(rgb in css,"Linux CSS missing "+rgb)
    for legacy in ("rgb(15,107,111)","rgb(28,138,141)","rgb(143,214,210)"):req(legacy not in css,"legacy teal leaked into Linux optical CSS")

    for p in ("scripts/validate_glaze_v1_2_android_optical_runtime.py","scripts/validate_glaze_v1_2_linux_optical_runtime.py"):
        c=text(p);req("nativeBackdropBlurClaim" in c and "performanceProfile" in c,"runtime validator incomplete: "+p)
    for p in ("acceptance/v1.2-android-optical-candidate.md","acceptance/v1.2-linux-optical-candidate.md"):
        c=text(p);req("Frost White" in c and "Ice Blue" in c and "Full" in c and "Reduced" in c and "Minimal" in c,"acceptance contract incomplete: "+p)
    print("GLAZE UI V1.2 bounded native Frosted Optical source contract: PASS")
    print("Stable authority: 1.1.0; full native parity remains unestablished")
if __name__=="__main__":main()

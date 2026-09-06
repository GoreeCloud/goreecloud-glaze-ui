#!/usr/bin/env python3
"""Rendered collision acceptance for V1.2 compact navigation accessibility reflow."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import validate_glaze_v1_2_living_glaze_rendered as living

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "v1.2" / "adaptive-navigation.candidate.json"
ARTIFACT = ROOT / "artifacts" / "glaze-v1.2-living-glaze-accessibility-reflow.json"
SCREENSHOT = "glaze-v1.2-living-glaze-accessibility-reflow.png"


class AcceptanceError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AcceptanceError(message)


def load_contract() -> dict:
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    require(value.get("version") == "1.2.0-candidate", "adaptive-navigation version drifted")
    require(value.get("lifecycle") == "candidate", "adaptive-navigation lifecycle drifted")
    require(value.get("consumerEligible") is False, "Candidate became consumer eligible")
    require(value.get("stableBaseline") == "1.1.0", "Stable baseline drifted")
    reflow = (value.get("navigationCapsule") or {}).get("accessibilityReflow") or {}
    for key in (
        "largeTextOrTouchAssistanceForcesInFlow",
        "stickyOrFloatingMayNotOccludeVisibleContent",
        "targetSizeMayNotBeReducedToPreserveFloatingLayout",
        "zeroVisibleControlIntersectionsRequired",
    ):
        require(reflow.get(key) is True, f"accessibility reflow contract weakened: {key}")
    return value


def set_mode(sid: str, *, text_200: bool, touch: bool) -> dict:
    return living.execute(
        sid,
        f"""
        const root=document.documentElement;
        delete root.dataset.glzTextScale;
        delete root.dataset.glzTouchAssistance;
        root.style.fontSize='';
        if ({str(text_200).lower()}) {{ root.dataset.glzTextScale='200'; root.style.fontSize='200%'; }}
        if ({str(touch).lower()}) root.dataset.glzTouchAssistance='true';
        window.scrollTo(0,0);
        void document.body.offsetWidth;
        const capsule=document.querySelector('#capsule');
        const rect=capsule.getBoundingClientRect();
        const clarity=[...document.querySelectorAll('[data-clarity]')];
        const intersects=(a,b)=>Math.max(a.left,b.left)<Math.min(a.right,b.right)&&Math.max(a.top,b.top)<Math.min(a.bottom,b.bottom);
        const collisions=clarity.filter(el=>intersects(rect,el.getBoundingClientRect())).map(el=>el.textContent.trim());
        const targets=[...capsule.querySelectorAll('button')].map(el=>{{const r=el.getBoundingClientRect();return {{w:r.width,h:r.height}};}});
        return {{
          position:getComputedStyle(capsule).position,
          viewport:innerWidth,
          scroll:document.documentElement.scrollWidth,
          left:rect.left,
          right:rect.right,
          top:rect.top,
          bottom:rect.bottom,
          collisions,
          targets
        }};
        """,
    )


def run() -> dict:
    load_contract()
    living.ART.mkdir(exist_ok=True)
    http = subprocess.Popen(
        [shutil.which("python3") or sys.executable, "-m", "http.server", str(living.WP), "--bind", living.HOST],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    drv = subprocess.Popen(
        [living.driver_path(), f"--port={living.DP}", "--allowed-ips="],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    sid = None
    try:
        living.wait_http(f"{living.SERVER}/{living.REF}")
        living.wait_driver()
        sid = living.session()
        living.request("POST", f"/session/{sid}/url", {"url": f"{living.SERVER}/{living.REF}"})
        end = time.monotonic() + 15
        while time.monotonic() < end:
            if living.execute(sid, "return document.readyState==='complete'&&window.livingGlazeReady===true"):
                break
            time.sleep(.1)
        else:
            raise AcceptanceError("Living Glaze lab not ready")

        living.cdp(
            sid,
            "Emulation.setDeviceMetricsOverride",
            {"width": 390, "height": 900, "deviceScaleFactor": 1, "mobile": False, "screenWidth": 390, "screenHeight": 900},
        )

        text_only = set_mode(sid, text_200=True, touch=False)
        touch_only = set_mode(sid, text_200=False, touch=True)
        combined = set_mode(sid, text_200=True, touch=True)

        for name, state in (("200% text", text_only), ("Touch Assistance", touch_only), ("combined accessibility enlargement", combined)):
            require(state["position"] not in {"sticky", "fixed"}, f"{name} left Navigation Capsule floating over content")
            require(state["scroll"] <= state["viewport"] + 1, f"{name} caused horizontal overflow")
            require(state["left"] >= -1 and state["right"] <= state["viewport"] + 1, f"{name} moved Navigation Capsule outside viewport")
            require(state["collisions"] == [], f"{name} Navigation Capsule intersects visible controls: {state['collisions']}")

        require(all(t["w"] >= 56 and t["h"] >= 56 for t in touch_only["targets"]), "Touch Assistance target floor fell below 56px")
        require(all(t["w"] >= 56 and t["h"] >= 56 for t in combined["targets"]), "combined accessibility target floor fell below 56px")

        living.execute(sid, "document.querySelector('#capsule').scrollIntoView({block:'end'});return true")
        screenshot = living.screenshot(sid, SCREENSHOT)
        return {
            "sourceRevision": living.revision(),
            "status": "passed",
            "candidateOnly": True,
            "stableBaseline": "1.1.0",
            "text200": text_only,
            "touchAssistance": touch_only,
            "combined": combined,
            "screenshot": screenshot,
            "acceptanceBoundary": "bounded-machine-rendered-only-no-human-or-physical-device-acceptance-implied",
        }
    finally:
        if sid:
            try:
                living.request("DELETE", f"/session/{sid}", timeout=5)
            except Exception:
                pass
        for proc in (drv, http):
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


def main() -> int:
    ARTIFACT.parent.mkdir(exist_ok=True)
    evidence = {"sourceRevision": living.revision(), "status": "started"}
    ARTIFACT.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    try:
        evidence = run()
        ARTIFACT.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print("GLAZE UI V1.2 accessibility navigation reflow collision acceptance passed")
        return 0
    except Exception as error:
        evidence["status"] = "failed"
        evidence["error"] = str(error)
        ARTIFACT.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print(f"GLAZE UI V1.2 accessibility navigation reflow acceptance failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

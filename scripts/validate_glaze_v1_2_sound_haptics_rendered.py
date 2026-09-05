#!/usr/bin/env python3
"""Rendered acceptance for bounded GLAZE UI V1.2 Sound and Haptics policy."""
from __future__ import annotations

import base64
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
HOST = "127.0.0.1"
WEB_PORT = 8806
DRIVER_PORT = 9556
SERVER = f"http://{HOST}:{WEB_PORT}"
DRIVER = f"http://{HOST}:{DRIVER_PORT}"
REFERENCE = "reference/v1.2/sound-haptics.html"
CONTRACT = ROOT / "contracts/v1.2/sound-haptics.candidate.json"
MODULE = ROOT / "js/glaze-v1.2-sound-haptics.candidate.mjs"
WORKFLOW = ROOT / ".github/workflows/glaze-v1.2-sound-haptics.yml"


class AcceptanceError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AcceptanceError(message)


def load(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected object in {path.relative_to(ROOT)}")
    return value


def validate_source() -> None:
    for path in (CONTRACT, MODULE, WORKFLOW, ROOT / REFERENCE):
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    contract = load(CONTRACT)
    require(contract.get("version") == "1.2.0-candidate", "sound/haptics version drifted")
    require(contract.get("lifecycle") == "candidate" and contract.get("consumerEligible") is False, "Candidate boundary drifted")
    require(contract.get("stableBaseline") == "1.1.0", "Stable baseline drifted")
    principles = contract.get("principles", {})
    require(principles.get("silenceIsDefault") is True, "silence is no longer default")
    require(principles.get("visualAndSemanticPresentationRemainComplete") is True, "visual/semantic completeness weakened")
    require(principles.get("essentialStateMayDependExclusivelyOnSoundOrHaptics") is False, "essential state became sensory-only")
    require(principles.get("priority") == ["semantic-state", "visual-feedback", "motion", "haptics", "sound"], "feedback priority drifted")
    require(set(contract.get("hapticTokens", [])) == {"haptic-tick","haptic-selection","haptic-snap","haptic-commit","haptic-warning","haptic-error"}, "haptic tokens drifted")
    require(set(contract.get("soundTokens", [])) == {"sound-confirm","sound-complete","sound-notify","sound-warning","sound-error","sound-connect","sound-disconnect"}, "sound tokens drifted")
    authority = contract.get("authorityBoundaries", {})
    require(authority.get("policyMayCreateProductState") is False, "feedback policy gained product-state authority")
    require(authority.get("policyMayUpgradeSecurityPrivacyIdentityRecoveryOrHealthTruth") is False, "feedback policy gained producer truth authority")
    require(authority.get("recoverySuccessRequiresProducerVerification") is True, "recovery verification guard weakened")
    require(authority.get("semanticStateMustPassThroughUnchanged") is True, "semantic-state passthrough weakened")
    execution = contract.get("candidateExecutionBoundary", {})
    for key in ("releasedAudioAssets","audioPlayback","navigatorVibrateCalls","physicalHapticExecution","platformCapabilityDetection","deviceSpecificMapping"):
        require(execution.get(key) is False, f"Candidate overclaimed/executed {key}")
    require(execution.get("policyPlanningOnly") is True, "Candidate is no longer policy-only")
    not_established = set(contract.get("evidenceBoundary", {}).get("notEstablished", []))
    require({"released-sound-assets","native-haptic-mappings","physical-haptic-quality","sound-device-quality","platform-capability-evidence","physical-device-acceptance","human-sensory-review","release-candidate","stable","consumer-conformance"}.issubset(not_established), "sound/haptics evidence boundary overclaims acceptance")

    source = MODULE.read_text(encoding="utf-8")
    for marker in ("HAPTIC_TOKENS", "SOUND_TOKENS", "planFeedback", "ROUTINE_SILENT", "blockedByVerification", "policyOnly: true"):
        require(marker in source, f"feedback policy marker missing: {marker}")
    lowered = source.lower()
    for forbidden in ("navigator.vibrate", "audiocontext", "new audio(", ".play(", "fetch(", "sendbeacon", "localstorage", "indexeddb"):
        require(forbidden not in lowered, f"Candidate feedback module crossed execution/persistence boundary: {forbidden}")

    reference = (ROOT / REFERENCE).read_text(encoding="utf-8")
    for marker in ("plays no audio and executes no vibration", "Recovery verification: pending", "Routine control — stay silent", "Unsupported haptics map to no-op"):
        require(marker in reference, f"reference marker missing: {marker}")
    lowered_ref = reference.lower()
    require("<audio" not in lowered_ref and "<video" not in lowered_ref, "reference embeds media playback")
    require("http://" not in lowered_ref and "https://" not in lowered_ref, "reference depends on remote media")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    require("validate_glaze_v1_2_sound_haptics_rendered.py" in workflow, "workflow does not run sound/haptics validator")
    require("github.event.pull_request.head.sha || github.sha" in workflow, "sound/haptics workflow is not exact-head pinned")


def request(method: str, path: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> Any:
    req = Request(f"{DRIVER}{path}", data=None if payload is None else json.dumps(payload).encode(), method=method, headers={"Content-Type":"application/json; charset=utf-8"})
    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as error:
        raise AcceptanceError(f"WebDriver HTTP {error.code}: {error.read().decode(errors='replace')}") from error
    except (URLError, TimeoutError) as error:
        raise AcceptanceError(f"WebDriver request failed: {error}") from error
    if not raw:
        return None
    value = json.loads(raw.decode()).get("value")
    if isinstance(value, dict) and value.get("error"):
        raise AcceptanceError(f"WebDriver {value.get('error')}: {value.get('message','')}")
    return value


def wait_http(url: str, seconds: float = 15) -> None:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except Exception:
            pass
        time.sleep(.15)
    raise AcceptanceError(f"HTTP endpoint not ready: {url}")


def chromedriver() -> str:
    for item in (shutil.which("chromedriver"), "/usr/bin/chromedriver", "/usr/local/share/chromedriver-linux64/chromedriver"):
        if item and Path(item).is_file():
            return str(item)
    raise AcceptanceError("chromedriver unavailable")


def execute(sid: str, script: str) -> Any:
    return request("POST", f"/session/{sid}/execute/sync", {"script":script,"args":[]})


def cdp(sid: str, cmd: str, params: dict[str, Any] | None = None) -> Any:
    return request("POST", f"/session/{sid}/goog/cdp/execute", {"cmd":cmd,"params":params or {}})


def screenshot(sid: str, name: str) -> None:
    encoded = request("GET", f"/session/{sid}/screenshot")
    require(isinstance(encoded, str) and encoded, "no screenshot bytes")
    ARTIFACTS.mkdir(exist_ok=True)
    path = ARTIFACTS / f"glaze-v1.2-sound-haptics-{name}.png"
    path.write_bytes(base64.b64decode(encoded))
    require(path.stat().st_size > 4000, f"invalid screenshot {path}")


def plan(sid: str, event: str, context: dict[str, Any]) -> dict[str, Any]:
    payload = json.dumps(context)
    value = execute(sid, f"return window.GlazeV12FeedbackPolicy.planFeedback({json.dumps(event)}, {payload});")
    require(isinstance(value, dict), f"feedback plan missing for {event}")
    return value


def main() -> int:
    http = driver = None
    sid: str | None = None
    try:
        validate_source()
        ARTIFACTS.mkdir(exist_ok=True)
        http = subprocess.Popen([sys.executable,"-m","http.server",str(WEB_PORT),"--bind",HOST,"--directory",str(ROOT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wait_http(f"{SERVER}/{REFERENCE}")
        driver = subprocess.Popen([chromedriver(),f"--port={DRIVER_PORT}","--allowed-ips=127.0.0.1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wait_http(f"{DRIVER}/status")
        value = request("POST","/session",{"capabilities":{"alwaysMatch":{"browserName":"chrome","goog:chromeOptions":{"args":["--headless=new","--no-sandbox","--disable-dev-shm-usage","--disable-background-networking","--disable-component-update","--disable-extensions","--disable-sync","--metrics-recording-only","--no-first-run","--window-size=900,1000"]}}}},timeout=60)
        require(isinstance(value, dict) and isinstance(value.get("sessionId"), str), "Chrome returned no session id")
        sid = value["sessionId"]
        request("POST",f"/session/{sid}/url",{"url":f"{SERVER}/{REFERENCE}"})
        for _ in range(100):
            if execute(sid,"return document.readyState") == "complete" and execute(sid,"return !!window.GlazeV12FeedbackPolicy"):
                break
            time.sleep(.1)
        require(execute(sid,"return !!window.GlazeV12FeedbackPolicy"), "feedback policy module did not initialize")

        resources = execute(sid,"return {media:document.querySelectorAll('audio,video').length,remote:performance.getEntriesByType('resource').map(x=>x.name).filter(x=>!x.startsWith(location.origin))}")
        require(resources.get("media") == 0 and not resources.get("remote"), f"reference loaded media/remote resources: {resources}")

        routine = plan(sid,"routine-button",{"semanticState":"ready","hapticCapability":True,"requestSound":True})
        require(routine.get("haptic") is None and routine.get("sound") is None and routine.get("semanticState") == "ready", f"routine control was not silent: {routine}")
        selection = plan(sid,"selection",{"semanticState":"selected","hapticCapability":True})
        require(selection.get("haptic") == "haptic-selection" and selection.get("sound") is None, f"selection routing drifted: {selection}")
        unsupported = plan(sid,"selection",{"semanticState":"selected","hapticCapability":False})
        require(unsupported.get("haptic") is None, f"unsupported haptics did not no-op: {unsupported}")
        complete = plan(sid,"complete",{"semanticState":"complete","hapticCapability":True,"requestedNotification":True})
        require(complete.get("haptic") == "haptic-commit" and complete.get("sound") == "sound-complete", f"requested completion routing drifted: {complete}")
        silent = plan(sid,"complete",{"semanticState":"complete","hapticCapability":True,"requestedNotification":True,"silentMode":True})
        require(silent.get("sound") is None and silent.get("semanticState") == "complete", f"silent mode did not suppress sound while preserving state: {silent}")
        off = plan(sid,"warning",{"semanticState":"warning","hapticCapability":True,"requestSound":True,"soundEnabled":False,"hapticsEnabled":False})
        require(off.get("sound") is None and off.get("haptic") is None and off.get("semanticState") == "warning", f"disabled channels changed functionality/state: {off}")
        sr = plan(sid,"warning",{"semanticState":"warning","hapticCapability":True,"requestSound":True,"screenReaderActive":True})
        require(sr.get("sound") is None, f"screen-reader audio priority was not preserved: {sr}")
        reduced = plan(sid,"selection",{"semanticState":"selected","hapticCapability":True,"sensoryReduction":True})
        require(reduced.get("haptic") is None and reduced.get("sound") is None, f"sensory reduction retained nonessential selection feedback: {reduced}")
        pending = plan(sid,"recovery-complete",{"semanticState":"Recovery verification: pending","hapticCapability":True,"requestedNotification":True,"authoritativeVerified":False})
        require(pending.get("blockedByVerification") is True and pending.get("haptic") is None and pending.get("sound") is None and pending.get("semanticState") == "Recovery verification: pending", f"unverified recovery planned success feedback: {pending}")
        verified = plan(sid,"recovery-complete",{"semanticState":"Recovery verification: confirmed","hapticCapability":True,"requestedNotification":True,"authoritativeVerified":True})
        require(verified.get("haptic") == "haptic-commit" and verified.get("sound") == "sound-complete", f"verified recovery feedback routing drifted: {verified}")
        bulk = plan(sid,"complete",{"semanticState":"10 files complete","hapticCapability":True,"requestedNotification":True,"repeatCount":10})
        require(bulk.get("coalesced") is True and bulk.get("repeatCount") == 10 and bulk.get("sound") == "sound-complete", f"bulk completion was not represented as one aggregate cue: {bulk}")
        screenshot(sid,"policy")

        cdp(sid,"Emulation.setDeviceMetricsOverride",{"width":320,"height":1200,"deviceScaleFactor":1,"mobile":False,"screenWidth":320,"screenHeight":1200})
        execute(sid,"document.documentElement.dataset.glzTextScale='200';document.documentElement.style.fontSize='200%';return true;")
        compact = execute(sid,"return {scroll:document.documentElement.scrollWidth,inner:innerWidth,minButton:Math.min(...Array.from(document.querySelectorAll('button')).map(b=>b.getBoundingClientRect().height))}")
        require(compact.get("scroll",9999) <= compact.get("inner",0) + 1, f"320px/200% reference overflowed: {compact}")
        require(compact.get("minButton",0) >= 48, f"feedback controls fell below 48px target: {compact}")
        screenshot(sid,"compact-200")

        print("GLAZE UI V1.2 Sound and Haptics rendered acceptance passed")
        return 0
    except AcceptanceError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    finally:
        if sid:
            try: request("DELETE",f"/session/{sid}")
            except Exception: pass
        for process in (driver,http):
            if process and process.poll() is None:
                process.terminate()
                try: process.wait(timeout=5)
                except subprocess.TimeoutExpired: process.kill()


if __name__ == "__main__":
    raise SystemExit(main())

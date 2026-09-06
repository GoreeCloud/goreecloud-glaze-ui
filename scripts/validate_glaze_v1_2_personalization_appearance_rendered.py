#!/usr/bin/env python3
"""Rendered acceptance for bounded GLAZE UI V1.2 Personalization and Appearance."""
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
WEB_PORT = 8804
DRIVER_PORT = 9554
SERVER = f"http://{HOST}:{WEB_PORT}"
DRIVER = f"http://{HOST}:{DRIVER_PORT}"
REFERENCE = "reference/v1.2/personalization-appearance.html"
CONTRACT = ROOT / "contracts/v1.2/personalization-appearance.candidate.json"
CSS = ROOT / "css/glaze-v1.2-personalization-appearance.candidate.css"
RUNTIME = ROOT / "js/glaze-v1.2-personalization.candidate.mjs"
ENTRYPOINT = ROOT / "css/glaze-v1.2.0-candidate.css"
WORKFLOW = ROOT / ".github/workflows/glaze-v1.2-personalization-appearance.yml"


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
    for path in (CONTRACT, CSS, RUNTIME, ENTRYPOINT, WORKFLOW, ROOT / REFERENCE):
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    contract = load(CONTRACT)
    require(contract.get("version") == "1.2.0-candidate", "personalization version drifted")
    require(contract.get("lifecycle") == "candidate" and contract.get("consumerEligible") is False, "Candidate boundary drifted")
    require(contract.get("stableBaseline") == "1.1.0", "Stable baseline drifted")
    require(contract.get("preferencePrecedence") == ["accessibility","platform-system","goreecloud-user","application-specific-when-allowed","glaze-default"], "preference precedence drifted")
    require(contract.get("appearance", {}).get("modes") == ["follow-system","light","dark","deep-dark"], "appearance mode set drifted")
    require(contract.get("appearance", {}).get("browserSystemAdapterImplemented") is True, "browser Follow System adapter missing")
    require(contract.get("appearance", {}).get("nativeSystemAdapterAcceptanceRequired") is True, "native system resolution acceptance boundary weakened")
    require(contract.get("accentProfiles", {}).get("allowed") == ["ice","slate","indigo","aqua","rose","amber"], "accent set drifted")
    require(contract.get("atmosphereProfiles", {}).get("allowed") == ["calm","balanced","expressive"], "atmosphere set drifted")
    require(contract.get("densityProfiles", {}).get("allowed") == ["comfortable","standard","productive","immersive"], "density set drifted")
    require(contract.get("densityProfiles", {}).get("minimumInteractiveTargetPx") == 48, "target floor drifted")
    require(contract.get("clarityProfiles", {}).get("allowed") == ["clear","balanced","dense"], "Clarity profile set drifted")
    persistence = contract.get("persistenceAndSync", {})
    require(persistence.get("persistenceAuthority") == "consumer-platform-adapter", "persistence authority drifted")
    require(persistence.get("adapterInterfaceImplemented") is True and persistence.get("webStorageAdapterHelperAvailable") is True, "bounded persistence adapter interface missing")
    require(persistence.get("directPersistenceOwnedByGlaze") is False, "Glaze improperly took direct persistence authority")
    require(persistence.get("crossDeviceSyncImplementedByThisCandidate") is False, "Candidate overclaimed cross-device sync")
    require(persistence.get("syncAuthority") == "separate-governed-goreecloud-sync-integration", "sync authority drifted")
    runtime_contract = contract.get("runtimeContract", {})
    for key in ("normalizationFailsClosedToGovernedDefaults","browserFollowSystemUsesPrefersColorScheme","systemChangesMayReResolveFollowSystem","manualAppearanceDoesNotTrackSystemChanges","persistenceAdapterIsOptional","malformedStoredPreferenceFallsBackSafely"):
        require(runtime_contract.get(key) is True, f"runtime contract weakened: {key}")
    prohibited = contract.get("prohibited", {})
    for key in ("semanticColorRemapping","securityOrPrivacyMeaningOverride","arbitraryIconPacks","arbitraryComponentGeometry","rawBlurSlider","rawSaturationSlider","rawShadowSlider","telemetryForPersonalization","remoteWallpaperSamplingRequirement"):
        require(prohibited.get(key) is True, f"fail-closed personalization prohibition drifted: {key}")
    not_established = set(contract.get("evidenceBoundary", {}).get("notEstablished", []))
    require({"native-follow-system-platform-adapter-acceptance","consumer-platform-persistence-acceptance","cross-device-preference-sync","wallpaper-sampling","human-visual-review","native-platform-parity","physical-device-acceptance","stable","consumer-conformance"}.issubset(not_established), "personalization evidence boundary overclaims acceptance")

    css = CSS.read_text(encoding="utf-8")
    for marker in ('data-glz-accent="ice"','data-glz-accent="rose"','data-glz-atmosphere="calm"','data-glz-atmosphere="expressive"','data-glz-density="productive"','data-glz-transparency="reduced"','data-glz-text-scale="200"','@media (forced-colors: active)','min-block-size: 48px'):
        require(marker in css, f"personalization CSS marker missing: {marker}")
    for forbidden in ("--glz1-danger", "--glz1-warning", "--glz1-success", "hue-rotate("):
        require(forbidden not in css, f"personalization layer attempted protected semantic/global remapping: {forbidden}")

    runtime = RUNTIME.read_text(encoding="utf-8")
    for marker in (
        "export function normalizePersonalization",
        "export function createBrowserSystemAppearanceAdapter",
        "export function createWebStoragePreferenceAdapter",
        "export function resolveAppearance",
        "export function applyPersonalization",
        "export function createPersonalizationController",
        "persistenceAuthority: 'consumer-platform-adapter'",
        "crossDeviceSyncAuthority: 'separate-governed-goreecloud-sync-integration'",
        "directCrossDeviceSyncImplemented: false",
        "directWallpaperSamplingImplemented: false",
    ):
        require(marker in runtime, f"personalization runtime marker missing: {marker}")
    for forbidden in ("fetch(", "XMLHttpRequest", "navigator.sendBeacon", "WebSocket", "indexedDB.open"):
        require(forbidden not in runtime, f"personalization runtime introduced ungoverned remote/persistent mechanism: {forbidden}")

    entry = ENTRYPOINT.read_text(encoding="utf-8")
    personal = '@import url("./glaze-v1.2-personalization-appearance.candidate.css");'
    accessibility = '@import url("./glaze-v1.2-accessibility.candidate.css");'
    require(personal in entry and accessibility in entry, "Candidate cascade missing personalization/accessibility layer")
    require(entry.index(personal) < entry.index(accessibility), "personalization must load before final accessibility authority")
    require(entry.strip().endswith(accessibility), "accessibility is no longer final in Candidate cascade")

    reference = (ROOT / REFERENCE).read_text(encoding="utf-8")
    for marker in (
        "Personalization changes expression",
        "Security review required",
        "No raw blur, saturation, or shadow sliders",
        "Follow System resolves through a bounded platform adapter",
        "Cross-device sync remains separately governed by GoreeCloud Sync",
        "createPersonalizationController",
        "createWebStoragePreferenceAdapter",
        "data-clarity=\"dense\"",
    ):
        require(marker in reference, f"personalization reference marker missing: {marker}")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    require("validate_glaze_v1_2_personalization_appearance_rendered.py" in workflow, "workflow does not run rendered validator")
    require("github.event.pull_request.head.sha || github.sha" in workflow, "workflow is not exact-head pinned")
    require("js/glaze-v1.2-personalization.candidate.mjs" in workflow, "workflow path filter does not include personalization runtime")


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
    path = ARTIFACTS / f"glaze-v1.2-personalization-appearance-{name}.png"
    path.write_bytes(base64.b64decode(encoded))
    require(path.stat().st_size > 4000, f"invalid screenshot {path}")


def wait_reference(sid: str) -> None:
    for _ in range(120):
        if execute(sid, "return document.readyState==='complete' && window.personalizationReady===true") is True:
            return
        time.sleep(.1)
    raise AcceptanceError("personalization reference did not become ready")


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
        value = request("POST","/session",{"capabilities":{"alwaysMatch":{"browserName":"chrome","goog:chromeOptions":{"args":["--headless=new","--no-sandbox","--disable-dev-shm-usage","--disable-background-networking","--disable-component-update","--disable-extensions","--disable-sync","--metrics-recording-only","--no-first-run","--window-size=900,1100"]}}}},timeout=60)
        require(isinstance(value, dict) and isinstance(value.get("sessionId"), str), "Chrome returned no session id")
        sid = value["sessionId"]
        request("POST",f"/session/{sid}/url",{"url":f"{SERVER}/{REFERENCE}"})
        wait_reference(sid)

        base = execute(sid,"""const r=getComputedStyle(document.documentElement),w=getComputedStyle(document.getElementById('semantic-warning')),a=getComputedStyle(document.getElementById('accent-card'));return {accent:r.getPropertyValue('--glz12-personal-accent').trim(),warningBorder:w.borderInlineStartColor||w.borderColor,accentBg:a.backgroundColor,persistence:window.glazePersonalizationReference.controller.persistenceEnabled};""")
        require(base.get("persistence") is True, "reference consumer did not opt into bounded persistence adapter")
        execute(sid,"window.glazePersonalizationReference.controller.set({accent:'rose'});return true;")
        rose = execute(sid,"""const r=getComputedStyle(document.documentElement),w=getComputedStyle(document.getElementById('semantic-warning')),a=getComputedStyle(document.getElementById('accent-card'));return {accent:r.getPropertyValue('--glz12-personal-accent').trim(),warningBorder:w.borderInlineStartColor||w.borderColor,accentBg:a.backgroundColor};""")
        require(base.get("accent") != rose.get("accent") and base.get("accentBg") != rose.get("accentBg"), "governed accent did not change decorative expression")
        require(base.get("warningBorder") == rose.get("warningBorder"), "accent personalization changed protected semantic warning state")
        screenshot(sid,"accent-isolation")

        execute(sid,"window.glazePersonalizationReference.controller.set({accent:'ice',atmosphere:'calm'});return true;")
        calm = execute(sid,"""const r=getComputedStyle(document.documentElement),s=getComputedStyle(document.getElementById('expression'));return {strength:parseFloat(r.getPropertyValue('--glz12-personal-atmosphere-strength')),image:s.backgroundImage};""")
        execute(sid,"window.glazePersonalizationReference.controller.set({atmosphere:'expressive'});return true;")
        expressive = execute(sid,"""const r=getComputedStyle(document.documentElement),s=getComputedStyle(document.getElementById('expression'));return {strength:parseFloat(r.getPropertyValue('--glz12-personal-atmosphere-strength')),image:s.backgroundImage};""")
        require(expressive.get("strength",0) > calm.get("strength",0), "atmosphere profiles are not meaningfully ordered")
        require(expressive.get("image") != "none", "expressive atmosphere did not render")
        execute(sid,"document.documentElement.dataset.glzTransparency='reduced';return true;")
        reduced = execute(sid,"return getComputedStyle(document.getElementById('expression')).backgroundImage")
        require(reduced == "none", f"Reduced Transparency did not suppress decorative atmosphere: {reduced}")
        screenshot(sid,"reduced-transparency")
        execute(sid,"document.documentElement.removeAttribute('data-glz-transparency');return true;")

        execute(sid,"window.glazePersonalizationReference.controller.set({density:'comfortable'});return true;")
        comfortable = execute(sid,"""const g=getComputedStyle(document.getElementById('personal-grid')),a=document.getElementById('action').getBoundingClientRect();return {gap:parseFloat(g.rowGap),height:a.height};""")
        execute(sid,"window.glazePersonalizationReference.controller.set({density:'productive'});return true;")
        productive = execute(sid,"""const g=getComputedStyle(document.getElementById('personal-grid')),a=document.getElementById('action').getBoundingClientRect();return {gap:parseFloat(g.rowGap),height:a.height};""")
        require(productive.get("gap",999) < comfortable.get("gap",0), "productive density did not reduce spacing")
        require(comfortable.get("height",0) >= 48 and productive.get("height",0) >= 48, "density violated 48px interaction floor")

        execute(sid,"window.glazePersonalizationReference.controller.set({clarity:'clear'});return true;")
        clear = execute(sid,"return document.documentElement.dataset.glazeClarity")
        execute(sid,"window.glazePersonalizationReference.controller.set({clarity:'dense'});return true;")
        dense = execute(sid,"return document.documentElement.dataset.glazeClarity")
        require(clear == "clear" and dense == "dense", "Living Frosted Clarity did not route through personalization controller")
        execute(sid,"window.glazePersonalizationReference.controller.set({clarity:'invalid-profile'});return true;")
        require(execute(sid,"return document.documentElement.dataset.glazeClarity") == "balanced", "invalid Clarity did not fail closed to Balanced")

        cdp(sid,"Emulation.setEmulatedMedia",{"media":"screen","features":[{"name":"prefers-color-scheme","value":"dark"}]})
        execute(sid,"window.glazePersonalizationReference.controller.set({appearance:'follow-system'});return true;")
        follow_dark = execute(sid,"return {preference:document.documentElement.dataset.glzAppearancePreference,resolved:document.documentElement.dataset.glzAppearance,media:matchMedia('(prefers-color-scheme: dark)').matches}")
        require(follow_dark == {"preference":"follow-system","resolved":"dark","media":True}, f"Follow System did not resolve dark: {follow_dark}")

        cdp(sid,"Emulation.setEmulatedMedia",{"media":"screen","features":[{"name":"prefers-color-scheme","value":"light"}]})
        time.sleep(.2)
        follow_light = execute(sid,"return {preference:document.documentElement.dataset.glzAppearancePreference,resolved:document.documentElement.dataset.glzAppearance,media:matchMedia('(prefers-color-scheme: dark)').matches}")
        require(follow_light == {"preference":"follow-system","resolved":"light","media":False}, f"Follow System did not react to system change: {follow_light}")

        execute(sid,"window.glazePersonalizationReference.controller.set({appearance:'deep-dark'});return true;")
        cdp(sid,"Emulation.setEmulatedMedia",{"media":"screen","features":[{"name":"prefers-color-scheme","value":"dark"}]})
        time.sleep(.2)
        manual = execute(sid,"return {preference:document.documentElement.dataset.glzAppearancePreference,resolved:document.documentElement.dataset.glzAppearance}")
        require(manual == {"preference":"deep-dark","resolved":"deep-dark"}, f"manual appearance tracked system unexpectedly: {manual}")
        screenshot(sid,"deep-dark")

        persisted = execute(sid,"""const r=window.glazePersonalizationReference;c=r.controller;r.persistenceAdapter.clear();c.set({appearance:'dark',accent:'rose',atmosphere:'calm',density:'comfortable',clarity:'dense'},{persist:true});return localStorage.getItem(r.storageKey);""")
        require(isinstance(persisted,str) and '"schemaVersion":1' in persisted and '"accent":"rose"' in persisted, "persistence adapter did not write versioned bounded envelope")
        execute(sid,"window.glazePersonalizationReference.controller.set({appearance:'light',accent:'ice',atmosphere:'expressive',density:'productive',clarity:'clear'});window.glazePersonalizationReference.controller.load();return true;")
        restored = execute(sid,"return {preference:document.documentElement.dataset.glzAppearancePreference,resolved:document.documentElement.dataset.glzAppearance,accent:document.documentElement.dataset.glzAccent,atmosphere:document.documentElement.dataset.glzAtmosphere,density:document.documentElement.dataset.glzDensity,clarity:document.documentElement.dataset.glazeClarity}")
        require(restored.get("preference") == "dark" and restored.get("resolved") == "dark" and restored.get("accent") == "rose" and restored.get("atmosphere") == "calm" and restored.get("density") == "comfortable" and restored.get("clarity") == "dense", f"persistence adapter round trip failed: {restored}")

        execute(sid,"localStorage.setItem(window.glazePersonalizationReference.storageKey,'{malformed');return true;")
        request("POST",f"/session/{sid}/url",{"url":f"{SERVER}/{REFERENCE}"})
        wait_reference(sid)
        fallback = execute(sid,"return {preference:document.documentElement.dataset.glzAppearancePreference,accent:document.documentElement.dataset.glzAccent,atmosphere:document.documentElement.dataset.glzAtmosphere,density:document.documentElement.dataset.glzDensity,clarity:document.documentElement.dataset.glazeClarity}")
        require(fallback == {"preference":"follow-system","accent":"ice","atmosphere":"balanced","density":"standard","clarity":"balanced"}, f"malformed stored preference did not fail closed: {fallback}")
        execute(sid,"window.glazePersonalizationReference.persistenceAdapter.clear();return true;")

        cdp(sid,"Emulation.setDeviceMetricsOverride",{"width":320,"height":1200,"deviceScaleFactor":1,"mobile":False,"screenWidth":320,"screenHeight":1200})
        execute(sid,"document.documentElement.dataset.glzTextScale='200';document.documentElement.style.fontSize='200%';window.glazePersonalizationReference.controller.set({density:'productive'});return true;")
        compact = execute(sid,"""const a=document.getElementById('action').getBoundingClientRect();return {scroll:document.documentElement.scrollWidth,inner:innerWidth,height:a.height,cols:getComputedStyle(document.getElementById('personal-grid')).gridTemplateColumns};""")
        require(compact.get("scroll",9999) <= compact.get("inner",0)+1, f"320px/200% text caused horizontal page overflow: {compact}")
        require(compact.get("height",0) >= 48, "large text/density combination violated target floor")
        require(" " not in str(compact.get("cols","")).strip(), f"large text did not resolve to single-column personalization composition: {compact}")
        screenshot(sid,"compact-200")

        print("GLAZE UI V1.2 Personalization and Appearance rendered adapter acceptance passed")
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

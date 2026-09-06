#!/usr/bin/env python3
"""Bounded browser-CI observations for V1.2 Living Frosted and Personalization paths.

These observations deliberately do not define or enforce production performance budgets.
"""
from __future__ import annotations

import base64
import json
import math
import platform
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
HOST, WEB_PORT, DRIVER_PORT = "127.0.0.1", 8813, 9563
SERVER, DRIVER = f"http://{HOST}:{WEB_PORT}", f"http://{HOST}:{DRIVER_PORT}"
CONTRACT = ROOT / "contracts/v1.2/performance-testing.candidate.json"
BUDGET = ROOT / "contracts/performance/glaze-v1-performance-budget.json"
LIVING_CONTRACT = ROOT / "contracts/v1.2/living-glaze.candidate.json"
PERSONALIZATION_CONTRACT = ROOT / "contracts/v1.2/personalization-appearance.candidate.json"
LIVING_REFERENCE = "reference/v1.2/living-glaze.html"
PERSONALIZATION_REFERENCE = "reference/v1.2/personalization-appearance.html"
LIVING_RUNTIME = ROOT / "js/glaze-v1.2-living-glaze.candidate.mjs"
PERSONALIZATION_RUNTIME = ROOT / "js/glaze-v1.2-personalization.candidate.mjs"


class AcceptanceError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AcceptanceError(message)


def load_json(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected object in {path.relative_to(ROOT)}")
    return value


def revision() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def finite(value: Any, label: str) -> float:
    require(isinstance(value, (int, float)) and math.isfinite(float(value)) and float(value) >= 0, f"invalid observation {label}: {value!r}")
    return float(value)


def validate_source() -> dict[str, Any]:
    for path in (CONTRACT, BUDGET, LIVING_CONTRACT, PERSONALIZATION_CONTRACT, LIVING_RUNTIME, PERSONALIZATION_RUNTIME, ROOT / LIVING_REFERENCE, ROOT / PERSONALIZATION_REFERENCE):
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")

    contract = load_json(CONTRACT)
    budget = load_json(BUDGET)
    living = load_json(LIVING_CONTRACT)
    personalization = load_json(PERSONALIZATION_CONTRACT)

    require(contract.get("version") == "1.2.0-candidate" and contract.get("lifecycle") == "candidate" and contract.get("consumerEligible") is False, "Performance Testing Candidate boundary drifted")
    require(contract.get("stableBaseline") == "1.1.0", "Performance Testing Stable baseline drifted")
    require(budget.get("status") == "revalidation-required", "canonical performance budget must remain revalidation-required")
    require(contract.get("canonicalBudgetBoundary", {}).get("numericRuntimeBudgetEstablished") is False, "numeric production runtime budget was overclaimed")
    require(contract.get("canonicalBudgetBoundary", {}).get("platformBudgetEstablished") is False, "accepted platform budget was overclaimed")
    require(contract.get("canonicalBudgetBoundary", {}).get("productionPerformanceAcceptanceEstablished") is False, "production performance acceptance was overclaimed")

    scope = [item.get("id") for item in contract.get("measurementScope", []) if isinstance(item, dict)]
    require("living-frosted-optical-and-tier-switch-observation" in scope, "Living Frosted performance observation scope missing")
    require("personalization-and-wallpaper-atmosphere-switch-observation" in scope, "Personalization performance observation scope missing")
    require("scripts/validate_glaze_v1_2_extended_performance.py" in contract.get("companionValidators", []), "extended performance companion is not governed")
    require(contract.get("implementation", {}).get("extendedValidator") == "scripts/validate_glaze_v1_2_extended_performance.py", "extended performance implementation binding drifted")

    rules = contract.get("rules", {})
    require(rules.get("measurementsAreObservations") is True and rules.get("passFailAgainstInventedNumericThresholds") is False, "performance observation boundary drifted")
    for key in (
        "browserCiEqualsProductionPerformance",
        "browserCiEqualsNativePerformance",
        "headlessBrowserMetricsEqualGpuOrCompositorBudget",
        "livingFrostedBrowserObservationEqualsPhysicalDevicePerformance",
        "personalizationBrowserObservationEqualsNativeAdapterPerformance",
        "localWallpaperDerivationObservationEqualsWallpaperSourceAdapterAcceptance",
    ):
        require(rules.get(key) is False, f"performance overclaim guard drifted: {key}")

    boundary = contract.get("evidenceBoundary", {})
    require(boundary.get("extendedLivingAndPersonalizationBrowserMeasurementsEstablished") is True, "extended browser observation evidence flag missing")
    require(boundary.get("phase5PerformanceTestingComplete") is False, "extended browser observations may not close G4 performance acceptance")
    not_established = set(boundary.get("notEstablished", []))
    require({
        "accepted-numeric-runtime-budget",
        "accepted-platform-performance-budget",
        "gpu-budget",
        "memory-budget",
        "power-budget",
        "thermal-budget",
        "living-frosted-physical-device-performance-acceptance",
        "personalization-native-adapter-performance-acceptance",
        "wallpaper-source-adapter-performance-acceptance",
        "physical-device-performance-acceptance",
        "production-performance-acceptance",
        "stable",
    }.issubset(not_established), "extended performance boundary lost blocking evidence classes")

    require(living.get("theme") == "Living Frosted" and living.get("consumerEligible") is False, "Living Frosted authority drifted")
    require(living.get("performanceTiers", {}).get("degradationOrder") == [3, 2, 1, 0], "Living Frosted degradation order drifted")
    require(personalization.get("consumerEligible") is False, "Personalization became consumer eligible")
    wallpaper = personalization.get("atmosphereProfiles", {}).get("wallpaperSampling", {})
    require(wallpaper.get("maximumAlpha") == 0.12 and wallpaper.get("maximumChromaRetention") == 0.28, "wallpaper atmosphere bounds drifted")
    require(wallpaper.get("directPixelAcquisitionOwnedByGlaze") is False and wallpaper.get("telemetryAllowed") is False, "wallpaper privacy boundary weakened")

    living_reference = (ROOT / LIVING_REFERENCE).read_text(encoding="utf-8")
    for marker in ("window.livingGlazeReady=true", "id=\"unknown\"", "id=\"capsule\""):
        require(marker in living_reference, f"Living performance hook missing: {marker}")
    personalization_reference = (ROOT / PERSONALIZATION_REFERENCE).read_text(encoding="utf-8")
    for marker in ("window.personalizationReady=true", "window.glazePersonalizationReference", "id=\"expression\"", "id=\"action\""):
        require(marker in personalization_reference, f"Personalization performance hook missing: {marker}")

    personalization_runtime = PERSONALIZATION_RUNTIME.read_text(encoding="utf-8")
    for forbidden in ("fetch(", "XMLHttpRequest", "navigator.sendBeacon", "WebSocket", "drawImage(", "getImageData("):
        require(forbidden not in personalization_runtime, f"Personalization performance path introduced ungoverned transport/pixel work: {forbidden}")
    return contract


def request(method: str, path: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> Any:
    req = Request(f"{DRIVER}{path}", data=None if payload is None else json.dumps(payload).encode(), method=method, headers={"Content-Type": "application/json; charset=utf-8"})
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
        raise AcceptanceError(f"WebDriver {value.get('error')}: {value.get('message', '')}")
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


def wait_driver() -> None:
    end = time.monotonic() + 15
    while time.monotonic() < end:
        try:
            status = request("GET", "/status")
            if isinstance(status, dict) and status.get("ready"):
                return
        except Exception:
            pass
        time.sleep(.2)
    raise AcceptanceError("chromedriver not ready")


def session() -> tuple[str, dict[str, Any]]:
    value = request("POST", "/session", {"capabilities": {"alwaysMatch": {"browserName": "chrome", "goog:chromeOptions": {"args": ["--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-background-networking", "--disable-component-update", "--disable-extensions", "--disable-sync", "--no-first-run", "--window-size=1280,1000"]}}}}, 60)
    require(isinstance(value, dict) and isinstance(value.get("sessionId"), str), "Chrome returned no session id")
    return value["sessionId"], value.get("capabilities", {}) if isinstance(value.get("capabilities"), dict) else {}


def execute(sid: str, script: str) -> Any:
    return request("POST", f"/session/{sid}/execute/sync", {"script": script, "args": []})


def execute_async(sid: str, script: str, timeout: int = 30) -> Any:
    return request("POST", f"/session/{sid}/execute/async", {"script": script, "args": []}, timeout)


def cdp(sid: str, cmd: str, params: dict[str, Any] | None = None) -> Any:
    return request("POST", f"/session/{sid}/goog/cdp/execute", {"cmd": cmd, "params": params or {}})


def navigate(sid: str, reference: str, ready_expression: str) -> None:
    request("POST", f"/session/{sid}/url", {"url": f"{SERVER}/{reference}"})
    end = time.monotonic() + 15
    while time.monotonic() < end:
        if execute(sid, f"return document.readyState==='complete' && ({ready_expression})"):
            return
        time.sleep(.1)
    raise AcceptanceError(f"reference did not initialize: {reference}")


def performance_metrics(sid: str) -> dict[str, float]:
    raw = cdp(sid, "Performance.getMetrics")
    require(isinstance(raw, dict) and isinstance(raw.get("metrics"), list), "Performance.getMetrics unavailable")
    wanted = {"Timestamp", "Documents", "Nodes", "LayoutCount", "RecalcStyleCount", "LayoutDuration", "RecalcStyleDuration", "ScriptDuration", "TaskDuration", "JSHeapUsedSize", "JSHeapTotalSize"}
    result: dict[str, float] = {}
    for metric in raw["metrics"]:
        if isinstance(metric, dict) and metric.get("name") in wanted and isinstance(metric.get("value"), (int, float)):
            result[str(metric["name"])] = float(metric["value"])
    require("Timestamp" in result, "Performance-domain snapshot missing Timestamp")
    return result


def metric_delta(before: dict[str, float], after: dict[str, float]) -> dict[str, float]:
    return {key: after[key] - before[key] for key in sorted(set(before) & set(after)) if key != "Timestamp"}


def screenshot(sid: str, name: str) -> str:
    encoded = request("GET", f"/session/{sid}/screenshot")
    require(isinstance(encoded, str) and encoded, f"no screenshot bytes for {name}")
    path = ARTIFACTS / f"glaze-v1.2-extended-performance-{name}.png"
    path.write_bytes(base64.b64decode(encoded))
    require(path.stat().st_size > 4000, f"invalid screenshot {path}")
    return path.name


def measure_living(sid: str) -> dict[str, Any]:
    navigate(sid, LIVING_REFERENCE, "window.livingGlazeReady===true")
    baseline = execute(sid, """const buttons=[...document.querySelectorAll('#capsule button')];return {clarity:document.documentElement.dataset.glazeClarity,tier:document.documentElement.dataset.glazeTier,targets:buttons.map(b=>b.getBoundingClientRect().height),unknown:document.querySelector('#unknown').dataset.backdropComplexity};""")
    require(baseline.get("clarity") == "balanced" and baseline.get("tier") == "3" and baseline.get("unknown") == "unknown", f"Living baseline drifted: {baseline}")
    require(all(float(value) >= 48 for value in baseline.get("targets", [])), "Living Navigation Capsule target floor weakened")
    before = performance_metrics(sid)
    observations = execute_async(sid, r"""
const done=arguments[arguments.length-1],root=document.documentElement,card=document.querySelector('#unknown'),buttons=[...document.querySelectorAll('#capsule button')];
const steps=[];for(const clarity of ['clear','balanced','dense'])for(const tier of ['3','2','1','0'])steps.push({clarity,tier});
const out=[];let index=0;
function next(){
  if(index>=steps.length){root.dataset.glazeClarity='balanced';root.dataset.glazeTier='3';requestAnimationFrame(()=>done(out));return;}
  const step=steps[index++],start=performance.now();root.dataset.glazeClarity=step.clarity;root.dataset.glazeTier=step.tier;void card.offsetWidth;
  requestAnimationFrame(()=>{const style=getComputedStyle(card);out.push({...step,switchToFrameMs:performance.now()-start,background:style.backgroundColor,backdrop:style.backdropFilter,border:style.borderColor,targetMin:Math.min(...buttons.map(b=>b.getBoundingClientRect().height)),text:card.textContent.trim()});next();});
}
next();
""")
    after = performance_metrics(sid)
    require(isinstance(observations, list) and len(observations) == 12, f"Living observation count drifted: {observations}")
    for item in observations:
        finite(item.get("switchToFrameMs"), f"living-{item.get('clarity')}-tier-{item.get('tier')}")
        require(float(item.get("targetMin", 0)) >= 48, f"Living transition weakened target geometry: {item}")
        require("Fail closed" in str(item.get("text", "")), f"Living deterministic-fallback content drifted: {item}")
    tier3 = [item for item in observations if item.get("tier") == "3"]
    require(len({item.get("background") for item in tier3}) == 3, "Living Clear/Balanced/Dense no longer produce distinct tier-3 material density")
    return {"baseline": baseline, "observations": observations, "performanceMetricDelta": metric_delta(before, after)}


def measure_personalization(sid: str) -> dict[str, Any]:
    navigate(sid, PERSONALIZATION_REFERENCE, "window.personalizationReady===true")
    execute(sid, "window.glazePersonalizationReference.persistenceAdapter.clear();window.glazePersonalizationReference.controller.set({appearance:'light',accent:'ice',atmosphere:'balanced',density:'standard',clarity:'balanced'});return true;")
    before = performance_metrics(sid)
    observations = execute_async(sid, r"""
const done=arguments[arguments.length-1],api=window.glazePersonalizationReference,root=document.documentElement,expression=document.getElementById('expression'),action=document.getElementById('action');
const steps=[
 {appearance:'light',accent:'ice',atmosphere:'calm',density:'comfortable',clarity:'clear'},
 {appearance:'dark',accent:'rose',atmosphere:'balanced',density:'standard',clarity:'balanced'},
 {appearance:'deep-dark',accent:'aqua',atmosphere:'expressive',density:'productive',clarity:'dense'}
];
const out=[];let index=0;
function next(){
 if(index>=steps.length){root.dataset.glzTransparency='reduced';requestAnimationFrame(()=>{const reduced=getComputedStyle(expression).backgroundImage;delete root.dataset.glzTransparency;done({steps:out,reducedTransparencyBackground:reduced});});return;}
 const step=steps[index++],start=performance.now();api.controller.set(step);void expression.offsetWidth;
 requestAnimationFrame(()=>{const style=getComputedStyle(expression);out.push({...step,switchToFrameMs:performance.now()-start,resolvedAppearance:root.dataset.glzAppearance,backgroundImage:style.backgroundImage,actionHeight:action.getBoundingClientRect().height});next();});
}
next();
""")
    require(isinstance(observations, dict) and isinstance(observations.get("steps"), list) and len(observations["steps"]) == 3, f"Personalization transition observations invalid: {observations}")
    for item in observations["steps"]:
        finite(item.get("switchToFrameMs"), f"personalization-{item.get('appearance')}")
        require(float(item.get("actionHeight", 0)) >= 48, f"Personalization transition weakened target floor: {item}")
        require(item.get("resolvedAppearance") == item.get("appearance"), f"manual appearance semantics drifted during performance observation: {item}")
    require(observations.get("reducedTransparencyBackground") == "none", "Reduced Transparency did not supersede Personalization atmosphere during observation")

    wallpaper = execute_async(sid, r"""
const done=arguments[arguments.length-1],api=window.glazePersonalizationReference,root=document.documentElement,expression=document.getElementById('expression'),start=performance.now();
const derived=api.applyWallpaperAtmosphere(document,{r:255,g:0,b:96});void expression.offsetWidth;
requestAnimationFrame(()=>done({deriveToFrameMs:performance.now()-start,derived,state:root.dataset.glzWallpaperAtmosphere||null,backgroundImage:getComputedStyle(expression).backgroundImage}));
""")
    require(isinstance(wallpaper, dict), f"wallpaper atmosphere observation invalid: {wallpaper}")
    finite(wallpaper.get("deriveToFrameMs"), "wallpaper-atmosphere-derive-to-frame")
    derived = wallpaper.get("derived") if isinstance(wallpaper.get("derived"), dict) else {}
    require(wallpaper.get("state") == "local-bounded", "wallpaper atmosphere state marker missing")
    require(float(derived.get("alpha", 1)) <= 0.12 and float(derived.get("chromaRetention", 1)) <= 0.28, "wallpaper atmosphere exceeded governed bounds")
    require("gradient" in str(wallpaper.get("backgroundImage", "")), "wallpaper atmosphere did not participate in rendered environment")
    after = performance_metrics(sid)
    execute(sid, "window.glazePersonalizationReference.applyWallpaperAtmosphere(document,null);window.glazePersonalizationReference.persistenceAdapter.clear();return true;")
    return {"transitions": observations, "wallpaperAtmosphere": wallpaper, "performanceMetricDelta": metric_delta(before, after)}


def main() -> int:
    ARTIFACTS.mkdir(exist_ok=True)
    evidence_path = ARTIFACTS / "glaze-v1.2-extended-performance-evidence.json"
    evidence: dict[str, Any] = {"sourceRevision": revision(), "status": "started"}
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    http = driver_process = None
    sid: str | None = None
    try:
        contract = validate_source()
        http = subprocess.Popen([sys.executable, "-m", "http.server", str(WEB_PORT), "--bind", HOST, "--directory", str(ROOT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wait_http(f"{SERVER}/{LIVING_REFERENCE}")
        driver_process = subprocess.Popen([chromedriver(), f"--port={DRIVER_PORT}", "--allowed-ips=127.0.0.1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wait_driver()
        sid, capabilities = session()
        request("POST", f"/session/{sid}/timeouts", {"script": 30000})
        cdp(sid, "Performance.enable")
        browser = cdp(sid, "Browser.getVersion")
        environment = execute(sid, "return {userAgent:navigator.userAgent,hardwareConcurrency:navigator.hardwareConcurrency||null,deviceMemory:navigator.deviceMemory||null,language:navigator.language||null};")
        evidence["environment"] = {
            "runnerPlatform": platform.platform(),
            "pythonVersion": platform.python_version(),
            "browser": browser,
            "webDriverCapabilities": capabilities,
            "navigator": environment,
            "viewport": [1280, 1000],
        }
        evidence["measurements"] = {
            "livingFrosted": measure_living(sid),
            "personalization": measure_personalization(sid),
        }
        evidence["screenshots"] = [
            screenshot(sid, "personalization-final"),
        ]
        navigate(sid, LIVING_REFERENCE, "window.livingGlazeReady===true")
        execute(sid, "document.documentElement.dataset.glazeClarity='dense';document.documentElement.dataset.glazeTier='3';return true;")
        evidence["screenshots"].append(screenshot(sid, "living-dense-tier3"))
        evidence["status"] = "passed"
        evidence["observationsOnly"] = True
        evidence["productionThresholdApplied"] = False
        evidence["phase5PerformanceTestingComplete"] = False
        evidence["notEstablished"] = contract.get("evidenceBoundary", {}).get("notEstablished", [])
        evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print("PASS: V1.2 Living Frosted and Personalization browser performance observations recorded; no production/native/device budget or acceptance is claimed.")
        return 0
    except Exception as error:
        evidence["status"] = "failed"
        evidence["error"] = str(error)
        evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print(f"V1.2 extended browser performance observation failed: {error}", file=sys.stderr)
        return 1
    finally:
        if sid:
            try:
                request("DELETE", f"/session/{sid}", timeout=5)
            except Exception:
                pass
        for process in (driver_process, http):
            if process is not None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except Exception:
                    process.kill()


if __name__ == "__main__":
    raise SystemExit(main())

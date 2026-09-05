#!/usr/bin/env python3
"""Rendered acceptance for bounded GLAZE UI V1.2 Performance Adaptation behavior."""
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
WEB_PORT = 8802
DRIVER_PORT = 9552
SERVER = f"http://{HOST}:{WEB_PORT}"
DRIVER = f"http://{HOST}:{DRIVER_PORT}"
REFERENCE = "reference/v1.2/performance-adaptation.html"
CONTRACT = ROOT / "contracts/v1.2/performance-adaptation.candidate.json"
BUDGET = ROOT / "contracts/performance/glaze-v1-performance-budget.json"
OPTICAL = ROOT / "css/glaze-v1.2-optical.candidate.css"
MOTION = ROOT / "css/glaze-v1.2-motion.candidate.css"
DEPTH = ROOT / "css/glaze-v1.2-depth-fallbacks.candidate.css"
ACCESSIBILITY = ROOT / "css/glaze-v1.2-accessibility.candidate.css"
MATRIX = ROOT / "contracts/accessibility/resolution-matrix.json"
ENTRYPOINT = ROOT / "css/glaze-v1.2.0-candidate.css"
WORKFLOW = ROOT / ".github/workflows/glaze-v1.2-performance-adaptation.yml"
PERFORMANCE_CSS = ROOT / "css/glaze-v1.2-performance-adaptation.candidate.css"


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
    for path in (CONTRACT, BUDGET, OPTICAL, MOTION, DEPTH, ACCESSIBILITY, MATRIX, ENTRYPOINT, WORKFLOW, ROOT / REFERENCE):
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")

    contract = load(CONTRACT)
    budget = load(BUDGET)
    require(contract.get("version") == "1.2.0-candidate", "performance contract version drifted")
    require(contract.get("lifecycle") == "candidate" and contract.get("consumerEligible") is False, "performance Candidate boundary drifted")
    require(contract.get("stableBaseline") == "1.1.0", "performance Stable baseline drifted")
    require(budget.get("status") == "revalidation-required", "canonical performance budget unexpectedly changed lifecycle")
    rules = budget.get("rules", {})
    require(rules.get("readableContentRequiresTransparency") is False, "performance budget now requires transparency for readable content")
    require(rules.get("nestedBackdropBlurAllowed") is False, "performance budget now allows nested backdrop blur")
    require(rules.get("effectsMayBeRemovedBeforeSemantics") is True, "performance budget no longer protects semantic priority")
    require("must be regenerated and accepted against exact V1 revisions" in budget.get("note", ""), "performance revalidation note drifted")

    boundary = contract.get("budgetBoundary", {})
    require(boundary.get("requiredSourceStatus") == "revalidation-required", "performance contract stopped binding canonical revalidation status")
    for key in ("numericRuntimeBudgetsEstablished", "platformBudgetsEstablished", "productionPerformanceAcceptanceEstablished"):
        require(boundary.get(key) is False, f"performance contract overclaims {key}")
    candidate_rules = contract.get("rules", {})
    for key in ("presentationMayDegradeBeforeSemantics", "consumerClaimBlocked"):
        require(candidate_rules.get(key) is True, f"performance rule drifted: {key}")
    for key in (
        "readableContentMayRequireTransparency", "nestedBackdropBlurAllowed", "performanceProfileMayChangeSemanticMeaning",
        "performanceProfileMayChangeReadingOrder", "performanceProfileMayShrinkInteractiveTargets",
        "performanceProfileMayHideRequiredActions", "accessibilityMayBeWeakenedByPerformanceProfile",
        "telemetryOrAnalyticsRequired", "automatedReferenceEvidenceEstablishesProductionPerformance",
        "automatedReferenceEvidenceEstablishesNativePerformanceParity",
    ):
        require(candidate_rules.get(key) is False, f"performance fail-closed rule drifted: {key}")
    require(contract.get("acceptance", {}).get("profiles") == ["full", "reduced", "minimal"], "performance profile order/set drifted")
    require(contract.get("acceptance", {}).get("minimumInteractiveTargetPx") == 48, "performance target floor drifted")
    not_established = set(contract.get("evidenceBoundary", {}).get("notEstablished", []))
    require({
        "numeric-runtime-performance-budget", "platform-performance-budget", "production-performance-acceptance",
        "physical-device-performance", "gpu-or-compositor-budget", "power-or-thermal-budget", "memory-budget",
        "complete-native-platform-performance-parity", "release-candidate", "stable", "consumer-conformance",
    }.issubset(not_established), "performance evidence boundary overclaims acceptance")

    optical = OPTICAL.read_text(encoding="utf-8")
    for marker in (
        'data-glz-material-performance="reduced"', 'data-glz-material-performance="minimal"',
        '--glz12-material-profile: reduced', '--glz12-material-profile: minimal',
        '--glz12-aura-opacity: 0', '--glz12-frost-dense-blur: 0px',
        'backdrop-filter: none', 'Semantics, focus, target size',
    ):
        require(marker in optical, f"optical performance authority marker missing: {marker}")
    motion = MOTION.read_text(encoding="utf-8")
    require('data-glz-material-performance="reduced"' in motion and 'data-glz-material-performance="minimal"' in motion, "motion performance profiles missing")
    require("--glz12-motion-standard-effective: 0ms" in motion and "--glz12-motion-travel-long: 0px" in motion, "minimal motion fallback drifted")
    depth = DEPTH.read_text(encoding="utf-8")
    require('data-glz-material-performance="minimal"' in depth and '[data-glz-depth-change]' in depth, "depth minimal fallback missing")
    require("transition: none" in depth and "transform: none" in depth, "depth minimal fallback no longer atomic")

    matrix = load(MATRIX)
    order = matrix.get("resolutionOrder", [])
    require("forced-colors" in order and "reduced-transparency" in order, "accessibility precedence authority incomplete")
    entry = ENTRYPOINT.read_text(encoding="utf-8").strip()
    require(entry.endswith('@import url("./glaze-v1.2-accessibility.candidate.css");'), "accessibility is no longer final in Candidate cascade")
    require(not PERFORMANCE_CSS.exists(), "duplicate performance CSS owner introduced; use existing optical/motion/depth authorities")

    reference = (ROOT / REFERENCE).read_text(encoding="utf-8")
    for marker in (
        "Browser observations validate graceful presentation fallback only",
        'id="performance-glaze"', 'data-glz-depth-change', 'id="performance-semantic"',
        'id="performance-primary"', 'window.setPerformanceProfile',
        "contains no FPS, frame-time, GPU, memory, thermal, power, or production threshold",
    ):
        require(marker in reference, f"performance reference marker missing: {marker}")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    require("validate_glaze_v1_2_performance_adaptation_rendered.py" in workflow, "performance workflow does not run rendered validator")
    require("github.event.pull_request.head.sha || github.sha" in workflow, "performance workflow is not exact-head pinned")


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
    last: Exception | None = None
    while time.monotonic() < end:
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except Exception as error:
            last = error
        time.sleep(.15)
    raise AcceptanceError(f"HTTP endpoint not ready: {last}")


def chromedriver() -> str:
    for item in (shutil.which("chromedriver"), "/usr/bin/chromedriver", "/usr/local/share/chromedriver-linux64/chromedriver"):
        if item and Path(item).is_file():
            return str(item)
    raise AcceptanceError("chromedriver unavailable")


def wait_driver() -> None:
    end = time.monotonic() + 15
    last: Exception | None = None
    while time.monotonic() < end:
        try:
            value = request("GET", "/status")
            if isinstance(value, dict) and value.get("ready"):
                return
        except Exception as error:
            last = error
        time.sleep(.2)
    raise AcceptanceError(f"chromedriver not ready: {last}")


def session() -> str:
    value = request("POST", "/session", {"capabilities": {"alwaysMatch": {"browserName": "chrome", "goog:chromeOptions": {"args": ["--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-background-networking", "--disable-component-update", "--disable-extensions", "--disable-sync", "--metrics-recording-only", "--no-first-run", "--window-size=1000,900"]}}}}, timeout=60)
    require(isinstance(value, dict) and isinstance(value.get("sessionId"), str), "Chrome returned no session id")
    return value["sessionId"]


def execute(sid: str, script: str) -> Any:
    return request("POST", f"/session/{sid}/execute/sync", {"script": script, "args": []})


def cdp(sid: str, cmd: str, params: dict[str, Any] | None = None) -> Any:
    return request("POST", f"/session/{sid}/goog/cdp/execute", {"cmd": cmd, "params": params or {}})


def viewport(sid: str, width: int, height: int) -> None:
    cdp(sid, "Emulation.setDeviceMetricsOverride", {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": False, "screenWidth": width, "screenHeight": height})


def media(sid: str, features: list[dict[str, str]]) -> None:
    cdp(sid, "Emulation.setEmulatedMedia", {"media": "screen", "features": features})


def navigate(sid: str) -> None:
    request("POST", f"/session/{sid}/url", {"url": f"{SERVER}/{REFERENCE}"})
    end = time.monotonic() + 15
    while time.monotonic() < end:
        if execute(sid, "return document.readyState==='complete' && window.performanceReferenceReady===true"):
            return
        time.sleep(.1)
    raise AcceptanceError("performance reference did not finish loading")


def screenshot(sid: str, name: str) -> None:
    encoded = request("GET", f"/session/{sid}/screenshot")
    require(isinstance(encoded, str) and encoded, "no screenshot bytes")
    ARTIFACTS.mkdir(exist_ok=True)
    path = ARTIFACTS / f"glaze-v1.2-performance-adaptation-{name}.png"
    path.write_bytes(base64.b64decode(encoded))
    require(path.stat().st_size > 5000, f"invalid screenshot {path}")


def reset_modes(sid: str) -> None:
    media(sid, [])
    execute(sid, """
const root=document.documentElement;
for(const name of ['data-glz-material-performance','data-glz-transparency','data-glz-motion','data-glz-contrast','data-glz-boundaries','data-mode']) root.removeAttribute(name);
document.getElementById('performance-primary').removeAttribute('data-demo-state');
window.setPerformanceProfile('full');
return true;
""")


def observe(sid: str, profile: str) -> dict[str, Any]:
    execute(sid, f"window.setPerformanceProfile({json.dumps(profile)});document.getElementById('performance-primary').setAttribute('data-demo-state','focus');document.getElementById('performance-primary').focus();return true;")
    value = execute(sid, """
const root=getComputedStyle(document.documentElement);
const glaze=getComputedStyle(document.getElementById('performance-glaze'));
const stageBefore=getComputedStyle(document.getElementById('performance-stage'),'::before');
const primary=document.getElementById('performance-primary');
const primaryStyle=getComputedStyle(primary);
const primaryRect=primary.getBoundingClientRect();
const semantic=document.getElementById('performance-semantic');
const semanticRect=semantic.getBoundingClientRect();
const semanticStyle=getComputedStyle(semantic);
const depth=getComputedStyle(document.getElementById('performance-glaze'));
return {
 profile: root.getPropertyValue('--glz12-material-profile').trim(),
 blurStandard: root.getPropertyValue('--glz12-blur-standard').trim(),
 frostDense: root.getPropertyValue('--glz12-frost-dense-blur').trim(),
 auraOpacity: root.getPropertyValue('--glz12-aura-opacity').trim(),
 auraLocalOpacity: root.getPropertyValue('--glz12-aura-local-opacity').trim(),
 auraFilter: stageBefore.filter,
 backdrop: glaze.backdropFilter || glaze.webkitBackdropFilter || 'none',
 motionStandard: root.getPropertyValue('--glz12-motion-standard-effective').trim(),
 motionTravelLong: root.getPropertyValue('--glz12-motion-travel-long').trim(),
 adaptiveOpacity: root.getPropertyValue('--glz12-profile-adaptive-opacity').trim(),
 depthTransition: depth.transitionDuration,
 depthTransform: depth.transform,
 targetWidth: primaryRect.width,
 targetHeight: primaryRect.height,
 focusOutlineWidth: primaryStyle.outlineWidth,
 activeElement: document.activeElement && document.activeElement.id,
 semanticVisible: semanticRect.width>0 && semanticRect.height>0,
 semanticBorder: semanticStyle.borderInlineStartWidth,
 semanticText: semantic.innerText,
 selectedPressed: document.getElementById('performance-selected').getAttribute('aria-pressed'),
 fieldValue: document.getElementById('performance-field').value,
 order: Array.from(document.querySelectorAll('#performance-glaze,#performance-semantic,#performance-field')).map(el=>el.id),
 overflow: Math.max(document.documentElement.scrollWidth,document.body.scrollWidth)-document.documentElement.clientWidth
};
""")
    require(isinstance(value, dict), f"invalid browser observation for {profile}")
    return value


def px(value: Any) -> float:
    text = str(value or "0").strip()
    require(text.endswith("px"), f"expected px value, got {text!r}")
    return float(text[:-2] or 0)


def main() -> int:
    http = driver = None
    sid: str | None = None
    observations: dict[str, Any] = {}
    try:
        validate_source()
        ARTIFACTS.mkdir(exist_ok=True)
        http = subprocess.Popen([sys.executable, "-m", "http.server", str(WEB_PORT), "--bind", HOST, "--directory", str(ROOT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wait_http(f"{SERVER}/{REFERENCE}")
        driver = subprocess.Popen([chromedriver(), f"--port={DRIVER_PORT}", "--allowed-ips=127.0.0.1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wait_driver()
        sid = session()
        viewport(sid, 1000, 900)
        navigate(sid)

        reset_modes(sid)
        full = observe(sid, "full")
        require(full.get("profile") == "full", f"full profile drifted: {full}")
        require(full.get("blurStandard") == "28px" and full.get("frostDense") == "44px", f"full optical reference calibration drifted: {full}")
        require(float(full.get("auraOpacity", -1)) == 1.0 and float(full.get("auraLocalOpacity", -1)) == 0.72, f"full Aura reference drifted: {full}")
        require(full.get("motionStandard") == "240ms" and full.get("motionTravelLong") == "32px", f"full motion reference drifted: {full}")
        observations["full"] = full
        screenshot(sid, "full")

        reset_modes(sid)
        reduced = observe(sid, "reduced")
        require(reduced.get("profile") == "reduced", f"reduced profile did not activate: {reduced}")
        require(reduced.get("blurStandard") == "20px" and reduced.get("frostDense") == "28px", f"reduced optical complexity did not decrease: {reduced}")
        require(float(reduced.get("auraOpacity", 2)) == 0.46 and float(reduced.get("auraLocalOpacity", 2)) == 0.33, f"reduced Aura complexity drifted: {reduced}")
        require(reduced.get("motionStandard") == "180ms" and reduced.get("motionTravelLong") == "16px", f"reduced motion complexity drifted: {reduced}")
        require(reduced.get("adaptiveOpacity") == "0", f"reduced adaptive optical presentation remained enabled: {reduced}")
        observations["reduced"] = reduced
        screenshot(sid, "reduced")

        reset_modes(sid)
        minimal = observe(sid, "minimal")
        require(minimal.get("profile") == "minimal", f"minimal profile did not activate: {minimal}")
        require(minimal.get("blurStandard") == "0px" and minimal.get("frostDense") == "0px", f"minimal blur was not removed: {minimal}")
        require(float(minimal.get("auraOpacity", 1)) == 0.0 and float(minimal.get("auraLocalOpacity", 1)) == 0.0, f"minimal Aura was not removed: {minimal}")
        require(minimal.get("backdrop") == "none", f"minimal frosted material retained backdrop filtering: {minimal}")
        require(minimal.get("motionStandard") == "0ms" and minimal.get("motionTravelLong") == "0px", f"minimal motion was not removed: {minimal}")
        require(set(str(minimal.get("depthTransition", "")).split(", ")) <= {"0s"}, f"minimal depth transition remained active: {minimal}")
        require(minimal.get("depthTransform") == "none", f"minimal depth transform remained active: {minimal}")
        observations["minimal"] = minimal
        screenshot(sid, "minimal")

        expected_order = ["performance-glaze", "performance-semantic", "performance-field"]
        for name, result in (("full", full), ("reduced", reduced), ("minimal", minimal)):
            require(result.get("semanticVisible") is True and "Warning" in str(result.get("semanticText", "")), f"{name} hid protected semantic state: {result}")
            require(float(str(result.get("semanticBorder", "0px")).replace("px", "") or 0) > 0, f"{name} removed semantic boundary: {result}")
            require(result.get("selectedPressed") == "true", f"{name} changed selected state semantics: {result}")
            require(result.get("fieldValue") == "Task context remains editable", f"{name} changed task content: {result}")
            require(result.get("order") == expected_order, f"{name} changed reading/DOM order: {result}")
            require(result.get("activeElement") == "performance-primary" and px(result.get("focusOutlineWidth")) >= 3, f"{name} lost focus visibility: {result}")
            require(float(result.get("targetWidth", 0)) >= 48 and float(result.get("targetHeight", 0)) >= 48, f"{name} shrank interactive target below 48px: {result}")
            require(float(result.get("overflow", 999)) <= 1, f"{name} introduced horizontal page overflow: {result}")

        viewport(sid, 320, 1100)
        reset_modes(sid)
        compact = observe(sid, "minimal")
        require(float(compact.get("overflow", 999)) <= 1, f"minimal compact reference overflows horizontally: {compact}")
        require(float(compact.get("targetHeight", 0)) >= 48, f"minimal compact target fell below 48px: {compact}")
        observations["minimalCompact"] = compact

        reset_modes(sid)
        execute(sid, "document.documentElement.dataset.glzTransparency='reduced';window.setPerformanceProfile('minimal');return true;")
        rt = observe(sid, "minimal")
        require(rt.get("backdrop") == "none" and float(rt.get("auraOpacity", 1)) == 0.0, f"Reduced Transparency was weakened by minimal performance profile: {rt}")
        require(rt.get("semanticVisible") is True and float(rt.get("targetHeight", 0)) >= 48, f"minimal+Reduced Transparency lost protected behavior: {rt}")
        observations["minimalReducedTransparency"] = rt

        reset_modes(sid)
        execute(sid, "window.setPerformanceProfile('minimal');return true;")
        media(sid, [{"name": "forced-colors", "value": "active"}])
        fc = observe(sid, "minimal")
        require(fc.get("backdrop") == "none" and float(fc.get("auraOpacity", 1)) == 0.0, f"Forced Colors was weakened by minimal performance profile: {fc}")
        require(fc.get("semanticVisible") is True and float(fc.get("targetHeight", 0)) >= 48, f"minimal+Forced Colors lost protected behavior: {fc}")
        observations["minimalForcedColors"] = fc

        report = {
            "schemaVersion": 1,
            "scope": "bounded-web-reference-observation",
            "performanceBudgetStatus": "revalidation-required",
            "productionPerformanceAcceptance": False,
            "numericRuntimeBudgetAcceptance": False,
            "nativePerformanceParity": False,
            "observations": observations,
        }
        (ARTIFACTS / "glaze-v1.2-performance-adaptation-observations.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("GLAZE UI V1.2 Performance Adaptation rendered acceptance passed (bounded Candidate evidence only).")
        return 0
    except AcceptanceError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    finally:
        if sid:
            try:
                request("DELETE", f"/session/{sid}")
            except Exception:
                pass
        for proc in (driver, http):
            if proc and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())

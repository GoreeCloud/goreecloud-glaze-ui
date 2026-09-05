#!/usr/bin/env python3
"""Bounded exact-head browser-CI performance measurements for GLAZE UI V1.2 Candidate."""
from __future__ import annotations

import base64
import json
import math
import platform
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
HOST, WEB_PORT, DRIVER_PORT = "127.0.0.1", 8805, 9555
SERVER, DRIVER = f"http://{HOST}:{WEB_PORT}", f"http://{HOST}:{DRIVER_PORT}"
CONTRACT = ROOT / "contracts/v1.2/performance-testing.candidate.json"
BUDGET = ROOT / "contracts/performance/glaze-v1-performance-budget.json"
ADAPTATION = ROOT / "contracts/v1.2/performance-adaptation.candidate.json"
DELEGATED = ROOT / "scripts/validate_glaze_v1_2_performance_adaptation_rendered.py"
REFERENCES = {
    "performance": "reference/v1.2/performance-adaptation.html",
    "motion": "reference/v1.2/motion.html",
    "visualization": "reference/v1.2/data-visualization.html",
    "productive": "reference/v1.2/productive-interfaces.html",
}
RUNTIMES = {
    "visualization": ROOT / "js/glaze-v1.2-data-visualization.candidate.mjs",
    "productive": ROOT / "js/glaze-v1.2-productive-interfaces.candidate.mjs",
}
W3C_ELEMENT = "element-6066-11e4-a52e-4f735466cecf"


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


def validate_source() -> dict[str, Any]:
    for path in (CONTRACT, BUDGET, ADAPTATION, DELEGATED, *[ROOT / p for p in REFERENCES.values()], *RUNTIMES.values()):
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    contract, budget, adaptation = load_json(CONTRACT), load_json(BUDGET), load_json(ADAPTATION)
    require(contract.get("version") == "1.2.0-candidate" and contract.get("lifecycle") == "candidate" and contract.get("consumerEligible") is False, "Performance Testing Candidate boundary drifted")
    require(contract.get("stableBaseline") == "1.1.0" and contract.get("phase") == "Phase 5 — Performance Testing", "Performance Testing lifecycle/phase drifted")
    boundary = contract.get("canonicalBudgetBoundary", {})
    require(budget.get("status") == boundary.get("requiredStatus") == "revalidation-required", "canonical performance budget must remain revalidation-required")
    require(boundary.get("numericRuntimeBudgetEstablished") is False and boundary.get("platformBudgetEstablished") is False and boundary.get("productionPerformanceAcceptanceEstablished") is False, "Performance Testing overclaimed accepted budgets")
    require("must be regenerated and accepted against exact V1 revisions" in budget.get("note", ""), "canonical budget regeneration requirement drifted")
    adaptation_boundary = adaptation.get("budgetBoundary", {})
    require(adaptation_boundary.get("requiredSourceStatus") == "revalidation-required", "Performance Adaptation stopped binding canonical budget status")
    rules = contract.get("rules", {})
    require(rules.get("exactRevisionRequired") is True and rules.get("measurementsAreObservations") is True, "measurement evidence boundary drifted")
    require(rules.get("passFailAgainstInventedNumericThresholds") is False, "Performance Testing may not invent pass/fail thresholds")
    require(rules.get("semanticsRemainHigherPriorityThanEffects") is True and rules.get("accessibilityTargetsRemainProtected") is True, "semantic/accessibility priority drifted")
    for key in (
        "browserCiEqualsProductionPerformance", "browserCiEqualsNativePerformance", "browserCiEqualsMobileGpuPerformance",
        "androidEmulatorEqualsPhysicalDevicePerformance", "headlessBrowserMetricsEqualGpuOrCompositorBudget",
        "testOnlyExpandedRowsEqualProductionLargeDatasetAcceptance", "fixtureVisualizationUpdateEqualsProductionChartUpdateAcceptance",
    ):
        require(rules.get(key) is False, f"Performance Testing overclaim guard drifted: {key}")
    require(contract.get("evidenceBoundary", {}).get("boundedBrowserCiMeasurementsEstablished") is True, "bounded browser-CI evidence flag drifted")
    require(contract.get("evidenceBoundary", {}).get("phase5PerformanceTestingComplete") is False, "bounded browser measurements may not close Phase 5 Performance Testing")
    not_established = set(contract.get("evidenceBoundary", {}).get("notEstablished", []))
    require({"accepted-numeric-runtime-budget", "accepted-platform-performance-budget", "gpu-budget", "memory-budget", "power-budget", "thermal-budget", "mobile-gpu-performance-acceptance", "physical-device-performance-acceptance", "production-performance-acceptance", "stable"}.issubset(not_established), "Performance Testing evidence boundary lost required blockers")

    motion = (ROOT / REFERENCES["motion"]).read_text(encoding="utf-8")
    for marker in ('id="search-toggle"', 'id="motion-search"', 'id="search-query"', 'data-glz-connected="search"', 'data-motion-reference-ready'):
        if marker == 'data-motion-reference-ready':
            require("motionReferenceReady" in motion, "Motion ready marker missing")
        else:
            require(marker in motion, f"Motion performance hook missing: {marker}")
    performance = (ROOT / REFERENCES["performance"]).read_text(encoding="utf-8")
    for marker in ('id="performance-primary"', 'id="performance-semantic"', 'window.setPerformanceProfile', 'contains no FPS, frame-time, GPU, memory, thermal, power, or production threshold'):
        require(marker in performance, f"Performance Adaptation hook missing: {marker}")
    visualization = (ROOT / REFERENCES["visualization"]).read_text(encoding="utf-8")
    require('id="viz-time-series"' in visualization and 'data-viz-point' in visualization and 'data-viz-range' in visualization, "Visualization measurement hooks missing")
    productive = (ROOT / REFERENCES["productive"]).read_text(encoding="utf-8")
    for marker in ('id="log-viewer"', 'id="scene-filtering"', 'data-record-body', 'id="sort-name"', 'id="table-search"'):
        require(marker in productive, f"Productive measurement hook missing: {marker}")
    for name, runtime in RUNTIMES.items():
        text = runtime.read_text(encoding="utf-8")
        for forbidden in ("fetch(", "XMLHttpRequest", "WebSocket", "localStorage", "sessionStorage", "indexedDB"):
            require(forbidden not in text, f"{name} runtime unexpectedly transports/persists data: {forbidden}")
    return contract


def run_delegated() -> str:
    result = subprocess.run([sys.executable, str(DELEGATED)], cwd=ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        raise AcceptanceError(f"delegated Performance Adaptation validator failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    return DELEGATED.name


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


def wait_http(url: str) -> None:
    end = time.monotonic() + 15
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
            value = request("GET", "/status")
            if isinstance(value, dict) and value.get("ready"):
                return
        except Exception:
            pass
        time.sleep(.2)
    raise AcceptanceError("chromedriver not ready")


def session() -> tuple[str, dict[str, Any]]:
    value = request("POST", "/session", {"capabilities": {"alwaysMatch": {"browserName": "chrome", "goog:chromeOptions": {"args": ["--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-background-networking", "--disable-component-update", "--disable-extensions", "--disable-sync", "--no-first-run", "--window-size=1280,960"]}}}}, 60)
    require(isinstance(value, dict) and isinstance(value.get("sessionId"), str), "Chrome returned no session id")
    return value["sessionId"], value.get("capabilities", {}) if isinstance(value.get("capabilities"), dict) else {}


def execute(sid: str, script: str) -> Any:
    return request("POST", f"/session/{sid}/execute/sync", {"script": script, "args": []})


def execute_async(sid: str, script: str, timeout: int = 30) -> Any:
    return request("POST", f"/session/{sid}/execute/async", {"script": script, "args": []}, timeout)


def cdp(sid: str, cmd: str, params: dict[str, Any] | None = None) -> Any:
    return request("POST", f"/session/{sid}/goog/cdp/execute", {"cmd": cmd, "params": params or {}})


def viewport(sid: str, width: int, height: int) -> None:
    cdp(sid, "Emulation.setDeviceMetricsOverride", {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": False, "screenWidth": width, "screenHeight": height})


def navigate(sid: str, reference: str, ready: str = "document.readyState==='complete'") -> None:
    request("POST", f"/session/{sid}/url", {"url": f"{SERVER}/{reference}"})
    end = time.monotonic() + 15
    while time.monotonic() < end:
        if execute(sid, f"return {ready}"):
            return
        time.sleep(.1)
    raise AcceptanceError(f"reference did not initialize: {reference}")


def find_element(sid: str, selector: str) -> str:
    value = request("POST", f"/session/{sid}/element", {"using": "css selector", "value": selector})
    require(isinstance(value, dict) and isinstance(value.get(W3C_ELEMENT), str), f"element not found: {selector}")
    return value[W3C_ELEMENT]


def click_element(sid: str, selector: str) -> None:
    element_id = find_element(sid, selector)
    request("POST", f"/session/{sid}/element/{element_id}/click", {})


def screenshot(sid: str, name: str) -> str:
    encoded = request("GET", f"/session/{sid}/screenshot")
    require(isinstance(encoded, str) and encoded, f"no screenshot bytes for {name}")
    ARTIFACTS.mkdir(exist_ok=True)
    path = ARTIFACTS / f"glaze-v1.2-performance-testing-{name}.png"
    path.write_bytes(base64.b64decode(encoded))
    require(path.stat().st_size > 5000, f"invalid screenshot {path}")
    return path.name


def finite_number(value: Any, label: str) -> float:
    require(isinstance(value, (int, float)) and math.isfinite(float(value)) and float(value) >= 0, f"invalid performance observation {label}: {value!r}")
    return float(value)


def summarize_intervals(values: Any, label: str) -> dict[str, Any]:
    require(isinstance(values, list) and len(values) >= 2, f"insufficient frame observations for {label}: {values!r}")
    numbers = [finite_number(value, label) for value in values]
    ordered = sorted(numbers)
    p95 = ordered[min(len(ordered) - 1, max(0, math.ceil(len(ordered) * .95) - 1))]
    return {
        "count": len(numbers),
        "minMs": min(numbers),
        "meanMs": statistics.fmean(numbers),
        "medianMs": statistics.median(numbers),
        "p95ObservedMs": p95,
        "maxMs": max(numbers),
    }


def performance_metrics(sid: str) -> dict[str, float]:
    raw = cdp(sid, "Performance.getMetrics")
    require(isinstance(raw, dict) and isinstance(raw.get("metrics"), list), "Performance.getMetrics unavailable")
    wanted = {"Timestamp", "Documents", "Nodes", "LayoutCount", "RecalcStyleCount", "LayoutDuration", "RecalcStyleDuration", "ScriptDuration", "TaskDuration", "JSHeapUsedSize", "JSHeapTotalSize"}
    result: dict[str, float] = {}
    for metric in raw["metrics"]:
        if isinstance(metric, dict) and metric.get("name") in wanted and isinstance(metric.get("value"), (int, float)):
            result[str(metric["name"])] = float(metric["value"])
    require("Timestamp" in result, "Performance-domain metric snapshot missing Timestamp")
    return result


def metric_delta(before: dict[str, float], after: dict[str, float]) -> dict[str, float]:
    return {key: after[key] - before[key] for key in sorted(set(before) & set(after)) if key != "Timestamp"}


def measure_interaction(sid: str) -> dict[str, Any]:
    viewport(sid, 1280, 960)
    navigate(sid, REFERENCES["motion"], "document.readyState==='complete' && document.documentElement.dataset.motionReferenceReady==='true'")
    execute(sid, "window.__glzPerfClick=undefined;document.getElementById('search-toggle').addEventListener('click',()=>{window.__glzPerfClick=performance.now()},{capture:true,once:true});return true;")
    click_element(sid, "#search-toggle")
    immediate = execute(sid, "return {open:document.getElementById('motion-search').dataset.open,expanded:document.getElementById('search-toggle').getAttribute('aria-expanded'),active:document.activeElement?.id||''};")
    require(immediate == {"open": "true", "expanded": "true", "active": "search-query"}, f"interaction semantics did not update immediately: {immediate}")
    next_frame = execute_async(sid, "const done=arguments[arguments.length-1];requestAnimationFrame(()=>done({eventToNextFrameMs:performance.now()-window.__glzPerfClick,state:document.getElementById('motion-search').dataset.open}));")
    require(isinstance(next_frame, dict) and next_frame.get("state") == "true", f"interaction next-frame state drifted: {next_frame}")
    finite_number(next_frame.get("eventToNextFrameMs"), "interaction-to-next-frame")
    return {"immediateState": immediate, **next_frame}


def measure_motion(sid: str) -> dict[str, Any]:
    execute(sid, "if(document.getElementById('motion-search').dataset.open==='true')document.getElementById('search-toggle').click();return true;")
    value = execute_async(sid, r"""
const done=arguments[arguments.length-1],btn=document.getElementById('search-toggle'),panel=document.getElementById('search-panel');
const frames=[];let start=null;const duration=getComputedStyle(panel).transitionDuration;
function step(t){if(start===null)start=t;frames.push(t);if(t-start>=650){const intervals=frames.slice(1).map((v,i)=>v-frames[i]);done({intervals,windowMs:t-start,transitionDuration:duration,open:document.getElementById('motion-search').dataset.open,expanded:btn.getAttribute('aria-expanded')});return;}requestAnimationFrame(step);}
requestAnimationFrame(()=>{btn.click();requestAnimationFrame(step);});
""", 10)
    require(isinstance(value, dict) and value.get("open") == "true" and value.get("expanded") == "true", f"connected-motion state drifted: {value}")
    finite_number(value.get("windowMs"), "motion-window")
    summary = summarize_intervals(value.get("intervals"), "connected-motion")
    return {"windowMs": value["windowMs"], "transitionDuration": value.get("transitionDuration"), "frameIntervals": summary}


def measure_profiles(sid: str) -> dict[str, Any]:
    navigate(sid, REFERENCES["performance"], "document.readyState==='complete' && window.performanceReferenceReady===true")
    observations: dict[str, Any] = {}
    for profile in ("full", "reduced", "minimal"):
        before = performance_metrics(sid)
        value = execute_async(sid, f"""
const done=arguments[arguments.length-1],start=performance.now();window.setPerformanceProfile({json.dumps(profile)});const target=document.getElementById('performance-primary'),semantic=document.getElementById('performance-semantic');target.focus();semantic.getBoundingClientRect();
requestAnimationFrame(()=>{{const tr=target.getBoundingClientRect(),sr=semantic.getBoundingClientRect(),cs=getComputedStyle(semantic),root=getComputedStyle(document.documentElement);done({{switchToFrameMs:performance.now()-start,profile:root.getPropertyValue('--glz12-material-profile').trim(),targetW:tr.width,targetH:tr.height,focus:document.activeElement?.id||'',semanticVisible:sr.width>0&&sr.height>0,semanticText:semantic.innerText,semanticBorder:cs.borderInlineStartWidth,overflow:Math.max(document.documentElement.scrollWidth,document.body.scrollWidth)-document.documentElement.clientWidth}});}});
""")
        after = performance_metrics(sid)
        require(isinstance(value, dict), f"invalid {profile} profile observation")
        finite_number(value.get("switchToFrameMs"), f"{profile}-profile-switch")
        require(float(value.get("targetW", 0)) >= 48 and float(value.get("targetH", 0)) >= 48, f"{profile} profile shrank accessible target: {value}")
        require(value.get("focus") == "performance-primary" and value.get("semanticVisible") is True and "Warning" in str(value.get("semanticText", "")), f"{profile} profile lost focus/semantic content: {value}")
        require(float(value.get("overflow", 999)) <= 1, f"{profile} profile caused page overflow: {value}")
        observations[profile] = {"renderObservation": value, "performanceMetricsBefore": before, "performanceMetricsAfter": after, "performanceMetricDelta": metric_delta(before, after)}
    return observations


def measure_visualization(sid: str) -> dict[str, Any]:
    navigate(sid, REFERENCES["visualization"], "document.readyState==='complete' && !!window.GlazeV12DataVisualization")
    value = execute_async(sid, r"""
const done=arguments[arguments.length-1],root=document.querySelector('#viz-time-series'),points=[...root.querySelectorAll('[data-viz-point]')],range=[...root.querySelectorAll('[data-viz-range]')].find(x=>x.dataset.vizRange==='24h');
const start=performance.now();points[1].click();range.click();requestAnimationFrame(()=>done({updateToFrameMs:performance.now()-start,selectedPoint:root.dataset.selectedPoint,range:root.dataset.range,pressed:points.map(p=>p.getAttribute('aria-pressed')),status:root.querySelector('[data-viz-range-status]').textContent}));
""")
    require(isinstance(value, dict) and value.get("range") == "24h", f"visualization fixture update drifted: {value}")
    require(isinstance(value.get("selectedPoint"), str) and bool(value.get("selectedPoint")), f"visualization selection did not update: {value}")
    finite_number(value.get("updateToFrameMs"), "visualization-fixture-update")
    require("unchanged" in str(value.get("status", "")), f"fixture visualization update changed authority boundary: {value}")
    return value


def measure_scrolling(sid: str) -> dict[str, Any]:
    navigate(sid, REFERENCES["productive"], "document.readyState==='complete' && !!window.GlazeV12ProductiveInterfaces")
    prep = execute(sid, r"""
const log=document.getElementById('log-viewer'),seed=log.querySelector('.glz12-log-entry');for(let i=0;i<300;i++){const c=seed.cloneNode(true);for(const e of c.querySelectorAll('[id]'))e.removeAttribute('id');c.querySelector('time').textContent=`11:${String(Math.floor(i/60)).padStart(2,'0')}:${String(i%60).padStart(2,'0')}`;c.querySelector('span').textContent=`Synthetic test-only fixture log entry ${i}.`;log.append(c);}log.scrollTop=0;return {clientHeight:log.clientHeight,scrollHeight:log.scrollHeight,max:log.scrollHeight-log.clientHeight,count:log.children.length};
""")
    require(isinstance(prep, dict) and float(prep.get("max", 0)) > 0 and int(prep.get("count", 0)) >= 300, f"scroll fixture expansion failed: {prep}")
    value = execute_async(sid, r"""
const done=arguments[arguments.length-1],log=document.getElementById('log-viewer'),max=log.scrollHeight-log.clientHeight,frames=[];let n=0;
function step(t){frames.push(t);n+=1;log.scrollTop=max*(n/60);if(n>=60){const intervals=frames.slice(1).map((v,i)=>v-frames[i]);done({intervals,endScrollTop:log.scrollTop,maxScrollTop:max,logLive:document.getElementById('scene-log-viewer').dataset.logLive});return;}requestAnimationFrame(step);}requestAnimationFrame(step);
""", 10)
    require(isinstance(value, dict), "invalid scrolling observation")
    require(float(value.get("endScrollTop", -1)) >= float(value.get("maxScrollTop", 0)) - 2, f"deterministic scroll did not reach live edge: {value}")
    summary = summarize_intervals(value.get("intervals"), "scrolling")
    return {"fixture": prep, "frameIntervals": summary, "endScrollTop": value.get("endScrollTop"), "maxScrollTop": value.get("maxScrollTop"), "logLiveState": value.get("logLive")}


def measure_large_table(sid: str) -> dict[str, Any]:
    prep = execute(sid, r"""
const root=document.getElementById('scene-filtering'),body=root.querySelector('[data-record-body]'),seed=body.querySelector('[data-record-row]');const desired=600;for(let i=body.querySelectorAll('[data-record-row]').length;i<desired;i++){const c=seed.cloneNode(true);c.removeAttribute('id');for(const e of c.querySelectorAll('[id]'))e.removeAttribute('id');c.dataset.name=`Synthetic Record ${String(i).padStart(4,'0')}`;c.dataset.searchText=`synthetic record ${i} fixture`;c.dataset.selected='false';const cells=c.querySelectorAll('td');if(cells.length>0)cells[0].textContent=c.dataset.name;body.append(c);}return {rows:body.querySelectorAll('[data-record-row]').length};
""")
    require(isinstance(prep, dict) and int(prep.get("rows", 0)) == 600, f"expanded table fixture count drifted: {prep}")
    value = execute(sid, r"""
const root=document.getElementById('scene-filtering'),sort=document.getElementById('sort-name'),search=document.getElementById('table-search');const t0=performance.now();sort.click();const sortMs=performance.now()-t0;search.value='synthetic record 599';const t1=performance.now();search.dispatchEvent(new Event('input',{bubbles:true}));const filterMs=performance.now()-t1;return {sortMs,filterMs,visible:root.dataset.visibleRecords,sortKey:root.dataset.sortKey,sortDirection:root.dataset.sortDirection,pageOverflow:Math.max(document.documentElement.scrollWidth,document.body.scrollWidth)-document.documentElement.clientWidth,rows:root.querySelectorAll('[data-record-row]').length};
""")
    require(isinstance(value, dict) and int(value.get("rows", 0)) == 600, f"expanded table measurement invalid: {value}")
    finite_number(value.get("sortMs"), "expanded-table-sort")
    finite_number(value.get("filterMs"), "expanded-table-filter")
    require(value.get("sortKey") == "name" and value.get("sortDirection") in ("ascending", "descending"), f"expanded table sort semantics drifted: {value}")
    require(int(value.get("visible", -1)) >= 1 and float(value.get("pageOverflow", 999)) <= 1, f"expanded table filter/containment drifted: {value}")
    return {"fixture": prep, **value}


def main() -> int:
    ARTIFACTS.mkdir(exist_ok=True)
    evidence_path = ARTIFACTS / "glaze-v1.2-performance-testing-evidence.json"
    evidence: dict[str, Any] = {"sourceRevision": revision(), "status": "started"}
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    http = driver_process = None
    sid: str | None = None
    try:
        contract = validate_source()
        evidence["delegatedValidator"] = run_delegated()
        http = subprocess.Popen([sys.executable, "-m", "http.server", str(WEB_PORT), "--bind", HOST, "--directory", str(ROOT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wait_http(f"{SERVER}/{REFERENCES['performance']}")
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
            "defaultViewport": [1280, 960],
        }
        evidence["measurements"] = {
            "interactionToNextFrame": measure_interaction(sid),
            "connectedMotionFrames": measure_motion(sid),
            "frostProfileSwitches": measure_profiles(sid),
            "visualizationFixtureUpdate": measure_visualization(sid),
            "scrolling": measure_scrolling(sid),
            "expandedTableWorkload": measure_large_table(sid),
        }
        evidence["screenshots"] = [screenshot(sid, "productive-expanded-workload")]
        evidence["status"] = "passed"
        evidence["boundedBrowserCiMeasurementsEstablished"] = True
        evidence["phase5PerformanceTestingComplete"] = False
        evidence["notEstablished"] = contract.get("evidenceBoundary", {}).get("notEstablished", [])
        evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print("PASS: GLAZE UI V1.2 bounded Performance Testing measurements recorded; canonical budget remains revalidation-required and no production threshold is claimed.")
        return 0
    except Exception as error:
        evidence["status"] = "failed"
        evidence["error"] = str(error)
        evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print(f"GLAZE UI V1.2 Performance Testing failed: {error}", file=sys.stderr)
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

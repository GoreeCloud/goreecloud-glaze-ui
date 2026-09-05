#!/usr/bin/env python3
"""Rendered acceptance for the bounded GLAZE UI V1.2 Signature component Candidate."""
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
WEB_PORT = 8796
DRIVER_PORT = 9546
SERVER = f"http://{HOST}:{WEB_PORT}"
DRIVER = f"http://{HOST}:{DRIVER_PORT}"
REFERENCE = "reference/v1.2/signature-components.html"
CONTRACT = ROOT / "contracts/v1.2/signature-components.candidate.json"
CSS = ROOT / "css/glaze-v1.2-signature-components.candidate.css"
RUNTIME = ROOT / "js/glaze-v1.2-signature.candidate.mjs"
ENTRYPOINT = ROOT / "css/glaze-v1.2.0-candidate.css"
WORKFLOW = ROOT / ".github/workflows/glaze-v1.2-signature-components.yml"
CATALOG = ROOT / "contracts/components/v1/catalog.json"
CORE_TOKENS = ROOT / "contracts/v1.2/core-tokens.candidate.json"

EXPECTED_COMPONENTS = [
    "GlzCapsule", "GlzMorphCard", "GlzSmartRail", "GlzAuroraSurface", "GlzUniversalSearch",
]


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


def revision() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def validate_source() -> None:
    for path in (CONTRACT, CSS, RUNTIME, ENTRYPOINT, WORKFLOW, ROOT / REFERENCE, CATALOG, CORE_TOKENS):
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")

    contract = load(CONTRACT)
    catalog = load(CATALOG)
    core = load(CORE_TOKENS)
    require(contract.get("version") == "1.2.0-candidate", "Signature contract version drifted")
    require(contract.get("lifecycle") == "candidate" and contract.get("consumerEligible") is False, "Signature Candidate boundary drifted")
    require(contract.get("stableBaseline") == "1.1.0", "Signature Stable baseline drifted")
    require(contract.get("tier") == "signature", "Signature tier drifted")
    require(catalog.get("tiers", {}).get("signature") == EXPECTED_COMPONENTS, "Stable Signature catalog drifted")
    require([item.get("id") for item in contract.get("components", [])] == EXPECTED_COMPONENTS, "V1.2 Signature family set/order drifted")

    rules = contract.get("universalRules", {})
    expected_true = (
        "clarityBeforeMaterial", "neutralGlassIsMaterialColorIsAccent", "nestedBackdropBlurProhibited",
        "durableReadingAndConsequentialContentBackdropDependencyProhibited",
        "semanticMeaningCannotDependOnlyOnAtmosphericColor", "focusDistinctFromCurrentOrSelectedState",
        "keyboardRequired", "reducedMotionRequired", "reducedTransparencyRequired",
        "increasedContrastRequired", "forcedColorsPlatformAuthoritative", "textScale200Required",
        "rtlWhereApplicable", "responsiveTransformationRequired", "noNewRuntimeDependency",
    )
    require(all(rules.get(key) is True for key in expected_true), "Signature universal rule drifted")
    require(rules.get("minimumTargetPx") == 48 and rules.get("assistedTargetPx") == 56, "Signature target floor drifted")

    boundary = contract.get("stateTokenBoundary", {})
    require(boundary.get("completeV12StateTokenOwnerEstablished") is False, "Signature tranche incorrectly assumes complete state-token authority")
    require(boundary.get("componentLocalStateRefinementOnly") is True, "Signature local state boundary drifted")
    require(boundary.get("mayImportTokensStatesJsonAsV12Authority") is False, "Signature tranche permits unrelated state-token authority")
    require(core.get("families", {}).get("state", {}).get("consumerClaimBlocked") is True, "Signature tranche assumes state-token consumer authority")

    runtime_boundary = contract.get("runtimeBoundary", {})
    require(runtime_boundary.get("stableRuntimeModified") is False, "Signature Candidate may not rewrite Stable runtime")
    require(runtime_boundary.get("pointerDestructiveConfirmationMustNotResetBetweenConsecutiveActivations") is True, "pointer confirmation rule missing")
    require(runtime_boundary.get("searchOpenStateMustSynchronizeDataAndAria") is True, "search state synchronization rule missing")

    css = CSS.read_text(encoding="utf-8")
    require("blur(" not in css.lower(), "Signature refinement layer must not introduce new blur calibration")
    for marker in (
        '.glz1-morph-card[data-reading="durable"]',
        '.glz1-rail-item[aria-current="page"]::after',
        '.glz1-search-result[data-confirming="true"]',
        '[data-glz-text-scale="200"]',
        '[data-glz-transparency="reduced"] .glz1-aurora::before',
        '@media (prefers-reduced-motion: reduce)',
        '@media (forced-colors: active)',
        '@media (max-width: 700px)',
    ):
        require(marker in css, f"Signature CSS marker missing: {marker}")

    runtime = RUNTIME.read_text(encoding="utf-8")
    for marker in (
        "bindV12Disclosure", "bindV12SmartRail", "bindV12UniversalSearch",
        'searchRoot.dataset.open = state.open ? "true" : "false"',
        'if (state.selectedIndex !== index) apply({ type: "select", index });',
        'destructive: node.dataset.destructive === "true"',
    ):
        require(marker in runtime, f"Signature runtime marker missing: {marker}")

    reference = (ROOT / REFERENCE).read_text(encoding="utf-8")
    for marker in (
        'id="signature-capsule"', 'id="signature-morph"', 'id="signature-rail"',
        'id="signature-aurora"', 'id="signature-search"', 'role="combobox"',
        'role="listbox"', 'data-destructive="true"', 'role="status"',
    ):
        require(marker in reference, f"Signature reference semantic marker missing: {marker}")

    impl = contract.get("implementation", {})
    require(impl.get("webLayer") == "css/glaze-v1.2-signature-components.candidate.css", "Signature CSS binding drifted")
    require(impl.get("candidateRuntime") == "js/glaze-v1.2-signature.candidate.mjs", "Signature runtime binding drifted")
    require(impl.get("reference") == REFERENCE, "Signature reference binding drifted")
    require(impl.get("renderedValidator") == "scripts/validate_glaze_v1_2_signature_components_rendered.py", "Signature validator binding drifted")
    require(impl.get("workflow") == ".github/workflows/glaze-v1.2-signature-components.yml", "Signature workflow binding drifted")

    entry = ENTRYPOINT.read_text(encoding="utf-8")
    chain = [
        '@import url("./glaze-v1.2-overlay-components.candidate.css")',
        '@import url("./glaze-v1.2-signature-components.candidate.css")',
        '@import url("./glaze-v1.2-accessibility.candidate.css")',
    ]
    require(all(item in entry for item in chain), "Candidate entrypoint missing Signature import chain")
    require([entry.index(item) for item in chain] == sorted(entry.index(item) for item in chain), "Signature/accessibility import order drifted")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    require("validate_glaze_v1_2_signature_components_rendered.py" in workflow, "Signature workflow does not invoke rendered validator")
    require("node --check js/glaze-v1.2-signature.candidate.mjs" in workflow, "Signature runtime syntax gate missing")
    require("github.event.pull_request.head.sha || github.sha" in workflow, "Signature workflow is not exact-head pinned")


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
            status = request("GET", "/status")
            if isinstance(status, dict) and status.get("ready"):
                return
        except Exception as error:
            last = error
        time.sleep(.2)
    raise AcceptanceError(f"chromedriver not ready: {last}")


def session() -> str:
    value = request("POST", "/session", {"capabilities": {"alwaysMatch": {"browserName": "chrome", "goog:chromeOptions": {"args": ["--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-background-networking", "--disable-component-update", "--disable-extensions", "--disable-sync", "--metrics-recording-only", "--no-first-run", "--window-size=1280,1100"]}}}}, timeout=60)
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
        if execute(sid, "return document.readyState === 'complete' && window.signatureReady === true"):
            return
        time.sleep(.1)
    raise AcceptanceError("Signature reference did not become ready")


def screenshot(sid: str, name: str) -> str:
    raw = request("GET", f"/session/{sid}/screenshot")
    require(isinstance(raw, str) and raw, f"no screenshot data for {name}")
    path = ARTIFACTS / name
    path.write_bytes(base64.b64decode(raw))
    return path.name


def baseline_acceptance(sid: str) -> dict[str, Any]:
    data = execute(sid, """
      const q=(s)=>document.querySelector(s), css=(s,p=null)=>getComputedStyle(q(s),p), box=(s)=>q(s).getBoundingClientRect();
      return {appearance:document.documentElement.dataset.glzAppearance,capsuleHeight:box('#signature-capsule').height,railHeight:box('#rail-home').height,morphBackdrop:css('#signature-morph').backdropFilter||css('#signature-morph').webkitBackdropFilter||'none',auroraBeforeDisplay:css('#signature-aurora','::before').display,searchHidden:q('#signature-search').hidden,searchDataOpen:q('#signature-search').dataset.open,searchExpanded:q('#signature-search-input').getAttribute('aria-expanded')};
    """)
    require(data["appearance"] == "light", "Signature reference must default to explicit light appearance")
    require(data["capsuleHeight"] >= 48 and data["railHeight"] >= 48, "Signature minimum target floor failed")
    require(data["morphBackdrop"] in ("none", ""), "durable Morph Card must not depend on backdrop blur")
    require(data["auroraBeforeDisplay"] != "none", "Aurora decorative field missing in baseline")
    require(data["searchHidden"] is True and data["searchDataOpen"] == "false" and data["searchExpanded"] == "false", "Search closed state is inconsistent")
    return data


def appearance_acceptance(sid: str) -> dict[str, Any]:
    data = execute(sid, """
      const q=(s)=>document.querySelector(s), out={};
      for(const appearance of ['light','dark','deep-dark']){document.documentElement.dataset.glzAppearance=appearance;const style=getComputedStyle(q('#signature-capsule'));out[appearance]={background:style.backgroundColor,color:style.color,border:style.borderTopColor};}
      document.documentElement.dataset.glzAppearance='light';return out;
    """)
    for name in ("light", "dark", "deep-dark"):
        require(name in data and data[name]["background"] not in ("", "rgba(0, 0, 0, 0)"), f"{name} Signature material did not render")
        require(data[name]["color"] not in ("", "rgba(0, 0, 0, 0)"), f"{name} Signature foreground did not render")
    return data


def interaction_acceptance(sid: str) -> dict[str, Any]:
    data = execute(sid, """
      const q=(s)=>document.querySelector(s);
      q('#signature-capsule').click();q('#signature-morph').click();
      q('#rail-home').focus();q('#rail-home').dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowDown',bubbles:true,cancelable:true}));const railFocus=document.activeElement?.id;
      q('#search-invoker').focus();q('#search-invoker').click();const searchOpened={hidden:q('#signature-search').hidden,dataOpen:q('#signature-search').dataset.open,expanded:q('#signature-search-input').getAttribute('aria-expanded'),panelDisplay:getComputedStyle(q('#signature-search-results')).display,focus:document.activeElement?.id};
      q('#signature-search-input').dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowDown',bubbles:true,cancelable:true}));const moved={selectedIndex:window.signatureControllers.search.getState().selectedIndex,focus:document.activeElement?.id};
      const destructive=q('#search-result-destructive');destructive.click();const confirm1={confirmationIndex:window.signatureControllers.search.getState().confirmationIndex,confirming:destructive.dataset.confirming,status:q('#search-status').textContent};destructive.click();const confirm2={confirmationIndex:window.signatureControllers.search.getState().confirmationIndex,lastExecutedIndex:window.signatureControllers.search.getState().lastExecutedIndex,confirming:destructive.dataset.confirming,status:q('#search-status').textContent};
      window.signatureControllers.search.close();q('#search-invoker').focus();q('#search-invoker').click();q('#signature-search-input').dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true,cancelable:true}));const escape={hidden:q('#signature-search').hidden,dataOpen:q('#signature-search').dataset.open,expanded:q('#signature-search-input').getAttribute('aria-expanded'),focus:document.activeElement?.id};
      return {capsuleExpanded:q('#signature-capsule').getAttribute('aria-expanded'),morphExpanded:q('#signature-morph').getAttribute('aria-expanded'),railFocus,searchOpened,moved,confirm1,confirm2,escape};
    """)
    require(data["capsuleExpanded"] == "true" and data["morphExpanded"] == "true", "Signature disclosure interaction failed")
    require(data["railFocus"] == "rail-files", "Smart Rail ArrowDown roving focus failed")
    opened = data["searchOpened"]
    require(opened["hidden"] is False and opened["dataOpen"] == "true" and opened["expanded"] == "true", "Search open state data/ARIA synchronization failed")
    require(opened["panelDisplay"] != "none" and opened["focus"] == "signature-search-input", "Search panel/focus opening failed")
    require(data["moved"]["selectedIndex"] == 0 and data["moved"]["focus"] == "search-result-files", "Search ArrowDown selection failed")
    require(data["confirm1"]["confirmationIndex"] == 2 and data["confirm1"]["confirming"] == "true", "first destructive pointer activation must request confirmation")
    require(data["confirm2"]["confirmationIndex"] is None and data["confirm2"]["lastExecutedIndex"] == 2, "second destructive pointer activation must execute")
    require(data["confirm2"]["confirming"] == "false" and data["confirm2"]["status"].startswith("Executed"), "destructive execution feedback failed")
    escape = data["escape"]
    require(escape["hidden"] is True and escape["dataOpen"] == "false" and escape["expanded"] == "false", "Search Escape close synchronization failed")
    require(escape["focus"] == "search-invoker", "Search Escape must restore invoker focus")
    return data


def adaptive_acceptance(sid: str) -> dict[str, Any]:
    viewport(sid, 390, 900)
    data = execute(sid, """
      const root=document.documentElement;root.dir='rtl';root.dataset.glzTextScale='200';root.dataset.glzTransparency='reduced';const q=(s)=>document.querySelector(s),copy=getComputedStyle(q('.glz1-capsule-copy strong')),rail=getComputedStyle(q('#signature-rail')),aurora=getComputedStyle(q('#signature-aurora'),'::before');return {direction:getComputedStyle(document.body).direction,copyWhiteSpace:copy.whiteSpace,railDirection:rail.flexDirection,railWidth:q('#signature-rail').getBoundingClientRect().width,viewportWidth:innerWidth,auroraDisplay:aurora.display};
    """)
    require(data["direction"] == "rtl", "RTL mode did not apply")
    require(data["copyWhiteSpace"] == "normal", "200% text must not retain capsule ellipsis clipping")
    require(data["railDirection"] == "row", "compact Smart Rail must adapt horizontally")
    require(data["railWidth"] <= data["viewportWidth"] + 1, "compact Smart Rail overflowed viewport")
    require(data["auroraDisplay"] == "none", "Reduced Transparency must remove Aurora atmosphere")
    return data


def forced_colors_acceptance(sid: str) -> dict[str, Any]:
    execute(sid, "document.documentElement.removeAttribute('data-glz-transparency'); return true")
    media(sid, [{"name": "forced-colors", "value": "active"}])
    data = execute(sid, "const q=(s)=>document.querySelector(s);return {auroraDisplay:getComputedStyle(q('#signature-aurora'),'::before').display,searchBackground:getComputedStyle(q('#signature-search-input')).backgroundColor};")
    require(data["auroraDisplay"] == "none", "Forced Colors must remove Aurora custom atmosphere")
    media(sid, [])
    return data


def run_rendered() -> dict[str, Any]:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    http = subprocess.Popen([shutil.which("python3") or sys.executable, "-m", "http.server", str(WEB_PORT), "--bind", HOST], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    driver = subprocess.Popen([chromedriver(), f"--port={DRIVER_PORT}", "--allowed-ips="], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sid = None
    try:
        wait_http(f"{SERVER}/{REFERENCE}"); wait_driver(); sid = session(); navigate(sid)
        baseline = baseline_acceptance(sid); appearances = appearance_acceptance(sid); interactions = interaction_acceptance(sid)
        wide_shot = screenshot(sid, "glaze-v1.2-signature-components-wide.png")
        adaptive = adaptive_acceptance(sid); compact_shot = screenshot(sid, "glaze-v1.2-signature-components-compact-rtl.png")
        forced = forced_colors_acceptance(sid)
        return {"sourceRevision": revision(), "reference": REFERENCE, "baseline": baseline, "appearances": appearances, "interactions": interactions, "adaptive": adaptive, "forcedColors": forced, "screenshots": [wide_shot, compact_shot]}
    finally:
        if sid:
            try: request("DELETE", f"/session/{sid}", timeout=5)
            except Exception: pass
        for process in (driver, http):
            process.terminate()
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired: process.kill()


def main() -> int:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    evidence_path = ARTIFACTS / "glaze-v1.2-signature-components-evidence.json"
    evidence: dict[str, Any] = {"sourceRevision": revision(), "status": "started"}
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    try:
        validate_source(); evidence = run_rendered(); evidence["status"] = "passed"
        evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print("GLAZE UI V1.2 Signature component Candidate acceptance passed"); return 0
    except Exception as error:
        evidence["status"] = "failed"; evidence["error"] = str(error)
        evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print(f"GLAZE UI V1.2 Signature component Candidate acceptance failed: {error}", file=sys.stderr); return 1


if __name__ == "__main__":
    raise SystemExit(main())

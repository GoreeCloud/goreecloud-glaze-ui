#!/usr/bin/env python3
"""Rendered acceptance for the bounded GLAZE UI V1.2 Foundation component Candidate."""
from __future__ import annotations

import base64
import json
import re
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
WEB_PORT = 8793
DRIVER_PORT = 9543
SERVER = f"http://{HOST}:{WEB_PORT}"
DRIVER = f"http://{HOST}:{DRIVER_PORT}"
REFERENCE = "reference/v1.2/foundation-components.html"
CONTRACT = ROOT / "contracts/v1.2/foundation-components.candidate.json"
CSS = ROOT / "css/glaze-v1.2-foundation-components.candidate.css"
ENTRYPOINT = ROOT / "css/glaze-v1.2.0-candidate.css"
WORKFLOW = ROOT / ".github/workflows/glaze-v1.2-foundation-components.yml"
CATALOG = ROOT / "contracts/components/v1/catalog.json"
CORE_TOKENS = ROOT / "contracts/v1.2/core-tokens.candidate.json"

EXPECTED_COMPONENTS = [
    "GlzButton", "GlzIconButton", "GlzTextField", "GlzSelect",
    "GlzCheckbox", "GlzRadio", "GlzSwitch", "GlzSlider",
]
TARGET_IDS = [
    "button-primary", "button-secondary", "button-subtle", "button-destructive",
    "button-selected", "button-loading", "button-disabled", "keyboard-button",
    "icon-button", "icon-button-selected", "icon-button-disabled",
    "field-normal-control", "field-error-control", "field-readonly-control", "field-disabled-control",
    "select-normal", "select-error", "checkbox-label", "checkbox-indeterminate-label",
    "checkbox-disabled-label", "radio-group", "switch-on-label", "switch-off-label",
    "switch-disabled-label", "slider",
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


def validate_source() -> None:
    for path in (CONTRACT, CSS, ENTRYPOINT, WORKFLOW, ROOT / REFERENCE, CATALOG, CORE_TOKENS):
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    contract = load(CONTRACT)
    catalog = load(CATALOG)
    core = load(CORE_TOKENS)
    require(contract.get("version") == "1.2.0-candidate", "foundation contract version drifted")
    require(contract.get("lifecycle") == "candidate" and contract.get("consumerEligible") is False, "foundation Candidate boundary drifted")
    require(contract.get("stableBaseline") == "1.1.0", "foundation Stable baseline drifted")
    require(contract.get("tier") == "foundation", "foundation tier drifted")
    require(catalog.get("tiers", {}).get("foundation") == EXPECTED_COMPONENTS, "Stable foundation catalog drifted")
    components = contract.get("components", [])
    require([item.get("id") for item in components] == EXPECTED_COMPONENTS, "V1.2 foundation family set/order drifted")
    require(core.get("families", {}).get("state", {}).get("consumerClaimBlocked") is True, "foundation tranche incorrectly assumes complete state-token authority")
    require(contract.get("stateTokenBoundary", {}).get("completeV12StateTokenOwnerEstablished") is False, "foundation tranche overclaims state-token completion")
    require(contract.get("stateTokenBoundary", {}).get("mayImportTokensStatesJsonAsV12Authority") is False, "foundation tranche permits unrelated state-token authority")
    rules = contract.get("universalRules", {})
    expected_true = (
        "clarityBeforeMaterial", "focusDistinctFromHoverAndSelection", "semanticMeaningCannotDependOnlyOnAtmosphericColor",
        "disabledSuppressesInteractionMotion", "loadingMustMaintainLayoutStability", "reducedMotionRequired",
        "reducedTransparencyRequired", "increasedContrastRequired", "forcedColorsPlatformAuthoritative",
        "textScale200Required", "rtlWhereApplicable", "nativeSemanticsPreferred", "noNewRuntimeDependency",
    )
    require(all(rules.get(key) is True for key in expected_true), "foundation universal rule drifted")
    require(rules.get("minimumTargetPx") == 48 and rules.get("assistedTargetPx") == 56, "foundation target floor drifted")
    impl = contract.get("implementation", {})
    require(impl.get("webLayer") == "css/glaze-v1.2-foundation-components.candidate.css", "foundation CSS binding drifted")
    require(impl.get("reference") == REFERENCE, "foundation reference binding drifted")
    require(impl.get("renderedValidator") == "scripts/validate_glaze_v1_2_foundation_components_rendered.py", "foundation validator binding drifted")
    require(impl.get("workflow") == ".github/workflows/glaze-v1.2-foundation-components.yml", "foundation workflow binding drifted")

    css = CSS.read_text(encoding="utf-8")
    for marker in (
        '[data-variant="primary"]', '[data-variant="subtle"]', '[data-variant="destructive"]',
        '[aria-pressed="true"]', '.glz12-control-status', '.glz12-field-status-mark',
        ':has(input[aria-invalid="true"])', ':has(input:checked)',
        'data-mode="increased-contrast"', '@media (forced-colors: active)',
    ):
        require(marker in css, f"foundation CSS marker missing: {marker}")
    require("animation: infinite" not in css.lower(), "foundation controls may not add autonomous infinite animation")

    reference = (ROOT / REFERENCE).read_text(encoding="utf-8")
    for marker in (
        'id="button-loading"', 'aria-busy="true"', 'id="field-error-input"', 'aria-invalid="true"',
        'id="checkbox-indeterminate"', 'data-indeterminate="true"', 'role="switch"', 'type="range"',
        'aria-describedby="slider-value"',
    ):
        require(marker in reference, f"foundation reference semantic marker missing: {marker}")

    entry = ENTRYPOINT.read_text(encoding="utf-8")
    chain = [
        '@import url("./glaze-v1.2-motion.candidate.css")',
        '@import url("./glaze-v1.2-foundation-components.candidate.css")',
        '@import url("./glaze-v1.2-accessibility.candidate.css")',
    ]
    require(all(item in entry for item in chain), "Candidate entrypoint missing foundation import chain")
    require([entry.index(item) for item in chain] == sorted(entry.index(item) for item in chain), "foundation/accessibility import order drifted")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    require("validate_glaze_v1_2_foundation_components_rendered.py" in workflow, "foundation workflow does not invoke rendered validator")
    require("github.event.pull_request.head.sha || github.sha" in workflow, "foundation workflow is not exact-head pinned")


def request(method: str, path: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> Any:
    req = Request(
        f"{DRIVER}{path}",
        data=None if payload is None else json.dumps(payload).encode(),
        method=method,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
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
    value = request("POST", "/session", {"capabilities": {"alwaysMatch": {
        "browserName": "chrome",
        "goog:chromeOptions": {"args": [
            "--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-background-networking",
            "--disable-component-update", "--disable-extensions", "--disable-sync", "--metrics-recording-only",
            "--no-first-run", "--window-size=1280,1100",
        ]},
    }}}, timeout=60)
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
        if execute(sid, "return document.readyState") == "complete":
            return
        time.sleep(.1)
    raise AcceptanceError("foundation reference did not finish loading")


def screenshot(sid: str, name: str) -> None:
    encoded = request("GET", f"/session/{sid}/screenshot")
    require(isinstance(encoded, str) and encoded, "no screenshot bytes")
    ARTIFACTS.mkdir(exist_ok=True)
    path = ARTIFACTS / f"glaze-v1.2-foundation-components-{name}.png"
    path.write_bytes(base64.b64decode(encoded))
    require(path.stat().st_size > 7000, f"invalid screenshot {path}")


def press_key(sid: str, key: str) -> None:
    request("POST", f"/session/{sid}/actions", {"actions": [{"type": "key", "id": "keyboard", "actions": [
        {"type": "keyDown", "value": key}, {"type": "keyUp", "value": key}
    ]}]})
    request("DELETE", f"/session/{sid}/actions")


STATE_JS = r"""
const ids = %s;
const targets = {};
for (const id of ids) {
  const el = document.getElementById(id);
  if (!el) { targets[id] = null; continue; }
  const r = el.getBoundingClientRect();
  targets[id] = {w:r.width,h:r.height};
}
const selected = getComputedStyle(document.getElementById('button-selected'));
const selectedIcon = getComputedStyle(document.getElementById('icon-button-selected'));
const cb = getComputedStyle(document.getElementById('checkbox-control'), '::after');
const ind = getComputedStyle(document.getElementById('checkbox-indeterminate-control'), '::after');
const radio = getComputedStyle(document.getElementById('radio-auto-control'), '::after');
const onThumb = getComputedStyle(document.getElementById('switch-on-thumb'));
const offThumb = getComputedStyle(document.getElementById('switch-off-thumb'));
const errorMark = document.querySelector('#field-error-control .glz12-field-status-mark').getBoundingClientRect();
const errorInput = document.getElementById('field-error-input');
const selectError = document.getElementById('select-error');
const icon = document.getElementById('icon-button');
const iconStyle = getComputedStyle(icon);
const primaryStyle = getComputedStyle(document.getElementById('button-primary'));
const disabledStyle = getComputedStyle(document.getElementById('button-disabled'));
return {
  ready: document.readyState,
  width: innerWidth,
  scrollWidth: document.documentElement.scrollWidth,
  appearance: document.documentElement.dataset.glzAppearance,
  dir: document.documentElement.dir || 'ltr',
  targets,
  selected: {shadow:selected.boxShadow, outline:selected.outlineWidth, aria:document.getElementById('button-selected').getAttribute('aria-pressed')},
  selectedIcon: {shadow:selectedIcon.boxShadow, name:document.getElementById('icon-button-selected').getAttribute('aria-label')},
  iconName: icon.getAttribute('aria-label'),
  iconBackdrop: iconStyle.backdropFilter || iconStyle.webkitBackdropFilter || 'none',
  checkbox: {checked:document.getElementById('checkbox').checked, opacity:parseFloat(cb.opacity), width:parseFloat(cb.width), height:parseFloat(cb.height)},
  indeterminate: {property:document.getElementById('checkbox-indeterminate').indeterminate, data:document.getElementById('checkbox-indeterminate').dataset.indeterminate, opacity:parseFloat(ind.opacity), width:parseFloat(ind.width), height:parseFloat(ind.height)},
  radio: {auto:document.getElementById('radio-auto').checked, manual:document.getElementById('radio-manual').checked, opacity:parseFloat(radio.opacity)},
  switchState: {on:document.getElementById('switch-on').checked, off:document.getElementById('switch-off').checked, onTransform:onThumb.transform, offTransform:offThumb.transform, role:document.getElementById('switch-on').getAttribute('role')},
  slider: {value:document.getElementById('slider').value, output:document.getElementById('slider-value').textContent.trim(), describedBy:document.getElementById('slider').getAttribute('aria-describedby')},
  loading: {busy:document.getElementById('button-loading').getAttribute('aria-busy'), text:document.getElementById('button-loading').textContent.replace(/\s+/g,' ').trim()},
  fieldError: {invalid:errorInput.getAttribute('aria-invalid'), describedBy:errorInput.getAttribute('aria-describedby'), message:document.getElementById('field-error-message').textContent.replace(/\s+/g,' ').trim(), markW:errorMark.width, markH:errorMark.height},
  selectError: {invalid:selectError.getAttribute('aria-invalid'), describedBy:selectError.getAttribute('aria-describedby')},
  readonly: document.querySelector('#field-readonly input').readOnly,
  fieldDisabled: document.querySelector('#field-disabled input').disabled,
  buttonDisabled: document.getElementById('button-disabled').disabled,
  buttonDisabledTransition: disabledStyle.transitionDuration,
  primary: {background:primaryStyle.backgroundColor, color:primaryStyle.color},
  activationCount: document.getElementById('keyboard-button').dataset.activationCount,
  activeId: document.activeElement && document.activeElement.id,
  activeFocusVisible: !!(document.activeElement && document.activeElement.matches && document.activeElement.matches(':focus-visible')),
  activeOutline: document.activeElement ? getComputedStyle(document.activeElement).outlineWidth : '0px'
};
""" % json.dumps(TARGET_IDS)


def state(sid: str) -> dict[str, Any]:
    value = execute(sid, STATE_JS)
    require(isinstance(value, dict), f"could not read foundation state: {value!r}")
    return value


def require_no_overflow(s: dict[str, Any]) -> None:
    width = int(s.get("width", 0))
    require(int(s.get("scrollWidth", width + 2)) <= width + 1, f"horizontal overflow: {s}")


def validate_targets(s: dict[str, Any]) -> None:
    for name, rect in s.get("targets", {}).items():
        require(isinstance(rect, dict), f"missing target {name}")
        require(float(rect.get("w", 0)) >= 48 and float(rect.get("h", 0)) >= 48, f"48 px target floor drifted for {name}: {rect}")


def validate_semantics(s: dict[str, Any]) -> None:
    require(s.get("ready") == "complete", f"page not ready: {s}")
    require(s["selected"]["aria"] == "true" and s["selected"]["shadow"] != "none", f"selected button lost structural cue: {s['selected']}")
    require(s["selectedIcon"]["shadow"] != "none" and s["selectedIcon"]["name"], "selected IconButton lost structure/name")
    require(s["iconName"], "IconButton accessible name missing")
    require(s["checkbox"]["checked"] is True and s["checkbox"]["opacity"] > .9 and s["checkbox"]["width"] > 0, f"checkbox geometry missing: {s['checkbox']}")
    require(s["indeterminate"]["property"] is True and s["indeterminate"]["data"] == "true" and s["indeterminate"]["opacity"] > .9 and s["indeterminate"]["height"] > 0, f"indeterminate geometry missing: {s['indeterminate']}")
    require(s["radio"]["auto"] is True and s["radio"]["opacity"] > .9, f"radio selected dot missing: {s['radio']}")
    require(s["switchState"]["on"] is True and s["switchState"]["off"] is False and s["switchState"]["onTransform"] != s["switchState"]["offTransform"], f"switch position does not carry state: {s['switchState']}")
    require(s["switchState"]["role"] == "switch", "Switch native semantic role missing")
    require(s["slider"]["value"] == s["slider"]["output"] and s["slider"]["describedBy"] == "slider-value", f"slider value output drifted: {s['slider']}")
    require(s["loading"]["busy"] == "true" and "Save" in s["loading"]["text"] and "Loading" in s["loading"]["text"], f"loading state lost label/status: {s['loading']}")
    require(s["fieldError"]["invalid"] == "true" and s["fieldError"]["describedBy"] == "field-error-message" and s["fieldError"]["message"] and s["fieldError"]["markW"] > 0 and s["fieldError"]["markH"] > 0, f"TextField error lacks associated non-color cue: {s['fieldError']}")
    require(s["selectError"]["invalid"] == "true" and s["selectError"]["describedBy"] == "select-error-message", f"Select error association drifted: {s['selectError']}")
    require(s["readonly"] is True and s["fieldDisabled"] is True and s["buttonDisabled"] is True, "read-only/disabled semantics drifted")
    require(s["buttonDisabledTransition"] == "0s", f"disabled button retained interaction transition: {s['buttonDisabledTransition']}")


def seconds(value: str) -> list[float]:
    result: list[float] = []
    for part in value.split(","):
        part = part.strip()
        match = re.fullmatch(r"([0-9.]+)(ms|s)", part)
        if match:
            number = float(match.group(1))
            result.append(number / 1000 if match.group(2) == "ms" else number)
    return result


def keyboard_acceptance(sid: str) -> None:
    navigate(sid)
    media(sid, [])
    execute(sid, "document.documentElement.dataset.glzAppearance='light'; document.documentElement.dir=''; return true;")

    press_key(sid, "\ue004")
    focused = state(sid)
    require(focused["activeId"] == "button-primary" and focused["activeFocusVisible"] is True and float(str(focused["activeOutline"]).replace("px", "") or 0) > 0, f"keyboard focus is not visibly established: {focused['activeId']}, {focused['activeOutline']}")

    execute(sid, "document.getElementById('keyboard-button').focus(); return true;")
    press_key(sid, "\ue007")
    require(state(sid)["activationCount"] == "1", "Enter did not activate native Button")

    execute(sid, "document.getElementById('checkbox').focus(); return true;")
    press_key(sid, "\ue00d")
    require(state(sid)["checkbox"]["checked"] is False, "Space did not toggle native Checkbox off")
    press_key(sid, "\ue00d")
    require(state(sid)["checkbox"]["checked"] is True, "Space did not toggle native Checkbox on")

    execute(sid, "document.getElementById('radio-auto').focus(); return true;")
    press_key(sid, "\ue014")
    radio = state(sid)["radio"]
    require(radio["manual"] is True and radio["auto"] is False, f"Arrow key did not move native Radio selection: {radio}")

    execute(sid, "document.getElementById('switch-off').focus(); return true;")
    before = state(sid)["switchState"]["offTransform"]
    press_key(sid, "\ue00d")
    time.sleep(.25)
    switched = state(sid)["switchState"]
    require(switched["off"] is True and switched["offTransform"] != before, f"Space did not continuously move settled Switch thumb: {switched}")

    execute(sid, "document.getElementById('slider').focus(); return true;")
    press_key(sid, "\ue014")
    slider = state(sid)["slider"]
    require(slider["value"] == "45" and slider["output"] == "45", f"Arrow key did not update native Slider/value output: {slider}")

    execute(sid, "document.getElementById('select-normal').focus(); return true;")
    press_key(sid, "\ue015")
    value = execute(sid, "return document.getElementById('select-normal').value")
    require(value == "dark", f"Arrow key did not move native Select value: {value!r}")


def main() -> int:
    http = driver = None
    sid: str | None = None
    try:
        validate_source()
        ARTIFACTS.mkdir(exist_ok=True)
        http = subprocess.Popen([sys.executable, "-m", "http.server", str(WEB_PORT), "--bind", HOST, "--directory", str(ROOT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wait_http(f"{SERVER}/{REFERENCE}")
        driver = subprocess.Popen([chromedriver(), f"--port={DRIVER_PORT}", "--allowed-ips=127.0.0.1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wait_driver()
        sid = session()
        media(sid, [])
        viewport(sid, 1280, 1100)
        navigate(sid)

        for appearance in ("light", "dark", "deep-dark"):
            execute(sid, f"document.documentElement.dataset.glzAppearance='{appearance}'; return true;")
            current = state(sid)
            validate_targets(current)
            validate_semantics(current)
            require_no_overflow(current)
            screenshot(sid, appearance)

        execute(sid, "document.documentElement.dataset.glzTransparency='reduced'; return true;")
        reduced = state(sid)
        validate_targets(reduced)
        validate_semantics(reduced)
        require(reduced["iconBackdrop"] == "none", f"Reduced Transparency retained foundation backdrop: {reduced['iconBackdrop']}")
        require_no_overflow(reduced)
        execute(sid, "delete document.documentElement.dataset.glzTransparency; return true;")

        execute(sid, "document.documentElement.dataset.mode='increased-contrast'; return true;")
        contrast_width = execute(sid, "return parseFloat(getComputedStyle(document.getElementById('button-secondary')).borderTopWidth)")
        require(float(contrast_width) >= 2, f"Increased Contrast did not strengthen foundation structure: {contrast_width}")
        execute(sid, "delete document.documentElement.dataset.mode; return true;")

        media(sid, [{"name": "prefers-reduced-motion", "value": "reduce"}])
        transition = execute(sid, "return getComputedStyle(document.getElementById('button-secondary')).transitionDuration")
        durations = seconds(str(transition))
        require(durations and max(durations) <= .12, f"Reduced Motion foundation transition too long: {transition}")
        media(sid, [])

        execute(sid, "document.documentElement.dir='rtl'; return true;")
        time.sleep(.25)
        rtl = state(sid)
        validate_targets(rtl)
        validate_semantics(rtl)
        require_no_overflow(rtl)
        execute(sid, "document.documentElement.dir='ltr'; return true;")
        time.sleep(.25)
        ltr_transform = execute(sid, "return getComputedStyle(document.getElementById('switch-on-thumb')).transform")
        execute(sid, "document.documentElement.dir='rtl'; return true;")
        time.sleep(.25)
        rtl_transform = execute(sid, "return getComputedStyle(document.getElementById('switch-on-thumb')).transform")
        require(ltr_transform != rtl_transform, f"Switch position did not adapt in settled RTL: {ltr_transform} / {rtl_transform}")
        execute(sid, "document.documentElement.dir=''; return true;")
        time.sleep(.25)

        media(sid, [{"name": "forced-colors", "value": "active"}])
        forced = state(sid)
        validate_targets(forced)
        require(forced["selected"]["shadow"] == "none" and float(str(forced["selected"]["outline"]).replace("px", "") or 0) > 0, f"Forced Colors selected state lost structural indicator: {forced['selected']}")
        require(forced["checkbox"]["opacity"] > .9 and forced["fieldError"]["markW"] > 0, "Forced Colors lost selection/error non-color cues")
        require_no_overflow(forced)
        screenshot(sid, "forced-colors")
        media(sid, [])

        viewport(sid, 390, 900)
        execute(sid, "document.documentElement.dataset.glzTextScale='200'; document.documentElement.style.fontSize='200%'; document.documentElement.dataset.glzAppearance='light'; return true;")
        large = state(sid)
        validate_targets(large)
        require_no_overflow(large)
        screenshot(sid, "compact-200")

        viewport(sid, 1280, 1100)
        execute(sid, "delete document.documentElement.dataset.glzTextScale; document.documentElement.style.fontSize=''; return true;")
        keyboard_acceptance(sid)

        print("GLAZE UI V1.2 Foundation components rendered validation: PASS")
        return 0
    except Exception as error:
        print(f"GLAZE UI V1.2 Foundation components rendered validation failed: {error}")
        return 1
    finally:
        if sid:
            try:
                request("DELETE", f"/session/{sid}")
            except Exception:
                pass
        for process in (driver, http):
            if process is not None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()


if __name__ == "__main__":
    raise SystemExit(main())

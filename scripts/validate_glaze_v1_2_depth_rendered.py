#!/usr/bin/env python3
"""Bounded rendered-web acceptance for the GLAZE UI V1.2 Depth and Elevation Candidate."""
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
WEB_PORT = 8791
DRIVER_PORT = 9541
SERVER = f"http://{HOST}:{WEB_PORT}"
DRIVER = f"http://{HOST}:{DRIVER_PORT}"
REFERENCE = "reference/v1.2/depth.html"
CONTRACT = ROOT / "contracts/v1.2/depth.candidate.json"
TOKENS = ROOT / "tokens/glaze-v1.2-depth.candidate.json"
CSS = ROOT / "css/glaze-v1.2-depth.candidate.css"
ENTRYPOINT = ROOT / "css/glaze-v1.2.0-candidate.css"
WORKFLOW = ROOT / ".github/workflows/glaze-v1.2-depth.yml"

EXPECTED = {
    "embedded": {"rank": 0, "y": 0, "blur": 4, "frost": 0, "edge": .03, "motion": 0},
    "base": {"rank": 1, "y": 0, "blur": 0, "frost": 0, "edge": .04, "motion": 0},
    "raised": {"rank": 2, "y": 8, "blur": 24, "frost": 18, "edge": .10, "motion": 140},
    "floating": {"rank": 3, "y": 14, "blur": 38, "frost": 18, "edge": .16, "motion": 160},
    "overlay": {"rank": 4, "y": 18, "blur": 52, "frost": 28, "edge": .20, "motion": 180},
    "modal": {"rank": 5, "y": 28, "blur": 80, "frost": 0, "edge": .22, "motion": 220},
    "hero": {"rank": 6, "y": 36, "blur": 110, "frost": 28, "edge": .18, "motion": 260},
}
FROSTED = {"raised": 18, "floating": 18, "overlay": 28, "hero": 28}


class AcceptanceError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AcceptanceError(message)


def validate_source() -> None:
    for path in (CONTRACT, TOKENS, CSS, ENTRYPOINT, WORKFLOW, ROOT / REFERENCE):
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    tokens = json.loads(TOKENS.read_text(encoding="utf-8"))
    require(contract.get("version") == "1.2.0-candidate", "depth contract version drifted")
    require(contract.get("lifecycle") == "candidate" and contract.get("consumerEligible") is False,
            "depth Candidate boundary drifted")
    require(contract.get("stableBaseline") == "1.1.0", "depth Stable baseline drifted")
    require(contract.get("hierarchy") == [
        "embedded", "base", "raised", "floating", "overlay", "modal", "spatialHero"
    ], "depth hierarchy drifted")
    rules = contract.get("rules", {})
    for key in (
        "depthBeforeDecoration", "frostIsNotMonotonicProxyForDepth",
        "consequentialModalMayRemainOpaque", "durableReadingMayRemainOpaque",
        "accessibilityOverridesOpticalDepth", "performanceProfilesPreserveHierarchy",
        "motionMaySupportDepthChangeButNotCarryMeaning",
    ):
        require(rules.get(key) is True, f"depth rule missing: {key}")
    for key in ("blueShadowAsDepthCueAllowed", "neonEdgeGlowAllowed",
                "nestedGlassShadowStackingAllowed", "nestedBackdropBlurAllowed"):
        require(rules.get(key) is False, f"depth prohibition drifted: {key}")

    calibration = contract.get("calibration", {})
    token_depth = tokens.get("depth", {})
    bindings = (
        ("embedded", "embedded"), ("base", "base"), ("raised", "raised"),
        ("floating", "floating"), ("overlay", "overlay"), ("modal", "modal"),
        ("spatialHero", "hero"),
    )
    for contract_key, rendered_key in bindings:
        expected = EXPECTED[rendered_key]
        item = calibration.get(contract_key, {})
        token = token_depth.get(contract_key, {})
        require(item.get("rank") == expected["rank"], f"{contract_key} rank drifted")
        require(item.get("shadowYpx") == expected["y"] and item.get("shadowBlurPx") == expected["blur"],
                f"{contract_key} shadow calibration drifted")
        require(item.get("frostBlurPx") == expected["frost"], f"{contract_key} frost calibration drifted")
        require(abs(float(item.get("edgeOpacity", -1)) - expected["edge"]) < 1e-6,
                f"{contract_key} edge calibration drifted")
        require(item.get("motionMs") == expected["motion"], f"{contract_key} motion calibration drifted")
        require(token.get("rank") == expected["rank"] and token.get("yPx") == expected["y"]
                and token.get("blurPx") == expected["blur"]
                and token.get("frostBlurPx") == expected["frost"],
                f"{contract_key} token drifted")

    require(calibration["modal"]["frost"] == "opaque-frost" and calibration["modal"]["frostBlurPx"] == 0,
            "modal must remain opaque-capable")
    require(calibration["spatialHero"]["shadowBlurPx"] > calibration["modal"]["shadowBlurPx"],
            "hero depth separation drifted")
    impl = contract.get("implementation", {})
    expected_impl = {
        "tokens": "tokens/glaze-v1.2-depth.candidate.json",
        "webLayer": "css/glaze-v1.2-depth.candidate.css",
        "webEntrypoint": "css/glaze-v1.2.0-candidate.css",
        "reference": REFERENCE,
        "renderedValidator": "scripts/validate_glaze_v1_2_depth_rendered.py",
        "workflow": ".github/workflows/glaze-v1.2-depth.yml",
    }
    for key, value in expected_impl.items():
        require(impl.get(key) == value, f"depth implementation binding drifted: {key}")

    css = CSS.read_text(encoding="utf-8")
    for marker in (
        '[data-glz-depth="embedded"]', '[data-glz-depth="modal"]',
        '[data-glz-depth="spatial-hero"]', "--glz12-depth-profile-shadow-scale: 0.64",
        "--glz12-depth-profile-frost-scale: 0.65", ".glz12-depth-owner .glz12-depth-child",
        "@media (forced-colors: active)", "prefers-reduced-motion: reduce",
    ):
        require(marker in css, f"depth CSS marker missing: {marker}")
    lower = css.lower()
    require("104 174 224 /" not in lower and "143 196 232 /" not in lower,
            "depth shadow may not use blue pigment")

    entry = ENTRYPOINT.read_text(encoding="utf-8")
    chain = [
        '@import url("./glaze-v1.2-geometry.candidate.css")',
        '@import url("./glaze-v1.2-depth.candidate.css")',
        '@import url("./glaze-v1.2-accessibility.candidate.css")',
    ]
    require(all(item in entry for item in chain), "Candidate entrypoint missing depth import chain")
    indexes = [entry.index(item) for item in chain]
    require(indexes == sorted(indexes), "depth/accessibility import order drifted")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    require("validate_glaze_v1_2_depth_rendered.py" in workflow,
            "depth workflow does not invoke rendered validator")
    require("github.event.pull_request.head.sha || github.sha" in workflow,
            "depth workflow is not exact-head pinned")


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
    for item in (shutil.which("chromedriver"), "/usr/bin/chromedriver",
                 "/usr/local/share/chromedriver-linux64/chromedriver"):
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
            "--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
            "--disable-background-networking", "--disable-component-update",
            "--disable-extensions", "--disable-sync", "--metrics-recording-only",
            "--no-first-run", "--window-size=1280,1000",
        ]},
    }}}, timeout=60)
    require(isinstance(value, dict) and isinstance(value.get("sessionId"), str),
            "Chrome returned no session id")
    return value["sessionId"]


def execute(sid: str, script: str) -> Any:
    return request("POST", f"/session/{sid}/execute/sync", {"script": script, "args": []})


def cdp(sid: str, cmd: str, params: dict[str, Any] | None = None) -> Any:
    return request("POST", f"/session/{sid}/goog/cdp/execute", {"cmd": cmd, "params": params or {}})


def viewport(sid: str, width: int, height: int) -> None:
    cdp(sid, "Emulation.setDeviceMetricsOverride", {
        "width": width, "height": height, "deviceScaleFactor": 1, "mobile": False,
        "screenWidth": width, "screenHeight": height,
    })


def media(sid: str, features: list[dict[str, str]]) -> None:
    cdp(sid, "Emulation.setEmulatedMedia", {"media": "screen", "features": features})


def navigate(sid: str) -> None:
    request("POST", f"/session/{sid}/url", {"url": f"{SERVER}/{REFERENCE}"})
    end = time.monotonic() + 15
    while time.monotonic() < end:
        if execute(sid, "return document.readyState") == "complete":
            return
        time.sleep(.1)
    raise AcceptanceError("depth reference did not finish loading")


def screenshot(sid: str, name: str) -> None:
    encoded = request("GET", f"/session/{sid}/screenshot")
    require(isinstance(encoded, str) and encoded, "no screenshot bytes")
    ARTIFACTS.mkdir(exist_ok=True)
    path = ARTIFACTS / f"glaze-v1.2-depth-{name}.png"
    path.write_bytes(base64.b64decode(encoded))
    require(path.stat().st_size > 7000, f"invalid screenshot {path}")


STATE_JS = r"""
const roleIds = ["embedded","base","raised","floating","overlay","modal","hero"];
const roles = {};
for (const id of roleIds) {
  const el = document.getElementById(id);
  const cs = getComputedStyle(el);
  const n = name => parseFloat(cs.getPropertyValue(name)) || 0;
  roles[id] = {
    rank: n("--glz12-depth-rank"),
    y: n("--glz12-depth-shadow-y"),
    blur: n("--glz12-depth-shadow-blur"),
    frost: n("--glz12-depth-frost-blur"),
    edge: n("--glz12-depth-edge-opacity"),
    motion: n("--glz12-depth-motion"),
    shadow: cs.boxShadow,
    backdrop: cs.backdropFilter || cs.webkitBackdropFilter || "none",
    border: cs.borderTopColor
  };
}
const root = getComputedStyle(document.documentElement);
const child = getComputedStyle(document.getElementById("nested-child"));
const floating = getComputedStyle(document.getElementById("floating"));
const actionRect = document.getElementById("depth-action").getBoundingClientRect();
return {
  ready: document.readyState,
  width: innerWidth,
  scrollWidth: document.documentElement.scrollWidth,
  appearance: document.documentElement.dataset.glzAppearance,
  shadowScale: parseFloat(root.getPropertyValue("--glz12-depth-profile-shadow-scale")) || 0,
  frostScale: parseFloat(root.getPropertyValue("--glz12-depth-profile-frost-scale")) || 0,
  edgeScale: parseFloat(root.getPropertyValue("--glz12-depth-edge-scale")) || 0,
  overlayAlpha: parseFloat(root.getPropertyValue("--glz12-depth-overlay-shadow-alpha")) || 0,
  roles,
  nestedShadow: child.boxShadow,
  nestedBackdrop: child.backdropFilter || child.webkitBackdropFilter || "none",
  floatingTransition: floating.transitionDuration,
  floatingTransform: floating.transform,
  action: {w: actionRect.width, h: actionRect.height}
};
"""


def state(sid: str) -> dict[str, Any]:
    value = execute(sid, STATE_JS)
    require(isinstance(value, dict), f"could not read depth state: {value!r}")
    return value


def require_no_overflow(s: dict[str, Any]) -> None:
    width = int(s.get("width", 0))
    require(int(s.get("scrollWidth", width + 2)) <= width + 1, f"horizontal overflow: {s}")


def parsed_blur(backdrop: str) -> float | None:
    match = re.search(r"blur\(([-0-9.]+)px\)", backdrop)
    return None if not match else float(match.group(1))


def validate_roles(s: dict[str, Any], *, expect_backdrop: bool = True) -> None:
    require(s.get("ready") == "complete", f"page not ready: {s}")
    roles = s.get("roles", {})
    for name, expected in EXPECTED.items():
        actual = roles.get(name, {})
        for key in ("rank", "y", "blur", "frost", "motion"):
            require(abs(float(actual.get(key, -999)) - expected[key]) < .2,
                    f"{name} {key} expected {expected[key]}, got {actual.get(key)}")
        require(abs(float(actual.get("edge", -1)) - expected["edge"]) < .005,
                f"{name} edge opacity drifted: {actual.get('edge')}")

    require(roles["base"]["blur"] < roles["raised"]["blur"] < roles["floating"]["blur"]
            < roles["overlay"]["blur"] < roles["modal"]["blur"] < roles["hero"]["blur"],
            "depth blur hierarchy drifted")
    for name in ("raised", "floating", "overlay", "modal", "hero"):
        require(roles[name]["shadow"] != "none", f"{name} lost rendered shadow")
    for name in ("embedded", "base", "modal"):
        require(roles[name]["backdrop"] == "none",
                f"{name} must remain non-backdrop-dependent: {roles[name]['backdrop']}")

    if expect_backdrop:
        frost_scale = float(s.get("frostScale", 1) or 1)
        for name, base_px in FROSTED.items():
            actual_px = parsed_blur(str(roles[name]["backdrop"]))
            expected_px = base_px * frost_scale
            require(actual_px is not None and abs(actual_px - expected_px) < .16,
                    f"{name} rendered frost expected {expected_px:g}px at scale {frost_scale:g}, "
                    f"got {roles[name]['backdrop']}")

    require(s.get("nestedShadow") == "none" and s.get("nestedBackdrop") == "none",
            f"nested depth stack not suppressed: {s.get('nestedShadow')} / {s.get('nestedBackdrop')}")
    action = s.get("action", {})
    require(float(action.get("w", 0)) >= 48 and float(action.get("h", 0)) >= 48,
            f"48 px target floor drifted: {action}")
    require_no_overflow(s)


def main() -> int:
    http = driver = None
    sid: str | None = None
    try:
        validate_source()
        ARTIFACTS.mkdir(exist_ok=True)
        http = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(WEB_PORT), "--bind", HOST, "--directory", str(ROOT)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        wait_http(f"{SERVER}/{REFERENCE}")
        driver = subprocess.Popen(
            [chromedriver(), f"--port={DRIVER_PORT}", "--allowed-ips=127.0.0.1"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        wait_driver()
        sid = session()
        media(sid, [])
        viewport(sid, 1280, 1000)
        navigate(sid)

        for appearance, alpha, edge_scale in (
            ("light", .14, 1.0), ("dark", .36, .76), ("deep-dark", .44, .64)
        ):
            execute(sid, f"document.documentElement.dataset.glzAppearance='{appearance}'; return true;")
            current = state(sid)
            validate_roles(current)
            require(abs(float(current.get("overlayAlpha", -1)) - alpha) < .01,
                    f"{appearance} overlay alpha drifted: {current.get('overlayAlpha')}")
            require(abs(float(current.get("edgeScale", -1)) - edge_scale) < .01,
                    f"{appearance} edge scale drifted: {current.get('edgeScale')}")
            for role in current["roles"].values():
                shadow = role["shadow"]
                require("104, 174, 224" not in shadow and "143, 196, 232" not in shadow,
                        f"{appearance} depth shadow became blue: {shadow}")
            screenshot(sid, appearance)

        execute(sid, "document.documentElement.dataset.glzAppearance='light'; "
                     "document.documentElement.dataset.glzMaterialPerformance='reduced'; return true;")
        reduced = state(sid)
        validate_roles(reduced)
        require(abs(float(reduced.get("shadowScale", -1)) - .64) < .01
                and abs(float(reduced.get("frostScale", -1)) - .65) < .01,
                f"reduced profile scales drifted: {reduced}")

        execute(sid, "document.documentElement.dataset.glzMaterialPerformance='full'; "
                     "document.documentElement.dataset.glzTransparency='reduced'; return true;")
        transparent = state(sid)
        validate_roles(transparent, expect_backdrop=False)
        require(all(transparent["roles"][name]["backdrop"] == "none"
                    for name in ("raised", "floating", "overlay", "hero")),
                "Reduced Transparency retained backdrop blur")
        require(transparent["roles"]["overlay"]["shadow"] != "none",
                "Reduced Transparency must preserve restrained structural shadow")

        execute(sid, "delete document.documentElement.dataset.glzTransparency; "
                     "document.documentElement.dataset.glzMaterialPerformance='minimal'; return true;")
        minimal = state(sid)
        require(all(role["shadow"] == "none" and role["backdrop"] == "none"
                    for role in minimal["roles"].values()),
                f"minimal profile retained optical depth: {minimal['roles']}")
        require_no_overflow(minimal)

        execute(sid, "document.documentElement.dataset.glzMaterialPerformance='full'; "
                     "document.getElementById('floating').dataset.glzDepthChange='elevated'; return true;")
        time.sleep(.25)
        elevated = state(sid)
        require(elevated.get("floatingTransform") != "none", "connected depth change did not render")
        execute(sid, "document.documentElement.dataset.mode='reduced-motion'; return true;")
        reduced_motion = state(sid)
        durations = {part.strip() for part in str(reduced_motion.get("floatingTransition", "")).split(",")}
        require(durations <= {"0s"}, f"Reduced Motion retained transition: {reduced_motion.get('floatingTransition')}")
        require(reduced_motion.get("floatingTransform") == "none",
                f"Reduced Motion retained depth transform: {reduced_motion.get('floatingTransform')}")
        execute(sid, "delete document.documentElement.dataset.mode; "
                     "document.getElementById('floating').dataset.glzDepthChange='resting'; return true;")

        media(sid, [{"name": "forced-colors", "value": "active"}])
        forced = state(sid)
        require(all(role["shadow"] == "none" and role["backdrop"] == "none"
                    for role in forced["roles"].values()),
                f"Forced Colors retained custom optical depth: {forced['roles']}")
        require_no_overflow(forced)
        screenshot(sid, "forced-colors")
        media(sid, [])

        viewport(sid, 390, 900)
        execute(sid, "document.documentElement.dataset.glzAppearance='light'; "
                     "document.documentElement.style.fontSize='200%'; "
                     "document.documentElement.dataset.glzTextScale='200'; return true;")
        compact = state(sid)
        require_no_overflow(compact)
        require(float(compact["action"]["w"]) >= 48 and float(compact["action"]["h"]) >= 48,
                f"compact 200% target floor drifted: {compact['action']}")
        screenshot(sid, "compact-200")

        print("GLAZE UI V1.2 Depth and Elevation rendered validation: PASS")
        print("Boundary: bounded web Depth Candidate only; native/compositor/human optical depth "
              "acceptance, RC, Stable, and consumer conformance remain unestablished.")
        return 0
    except Exception as error:
        print(f"GLAZE UI V1.2 Depth and Elevation rendered validation failed: {error}", file=sys.stderr)
        return 1
    finally:
        if sid:
            try:
                request("DELETE", f"/session/{sid}", timeout=5)
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

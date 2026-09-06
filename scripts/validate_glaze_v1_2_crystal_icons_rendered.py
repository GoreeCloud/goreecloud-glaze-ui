#!/usr/bin/env python3
"""Bounded rendered-web acceptance for the GLAZE UI V1.2 Crystal Icon System Candidate."""
from __future__ import annotations

import base64, json, shutil, subprocess, sys, time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
HOST = "127.0.0.1"
WEB_PORT = 8788
DRIVER_PORT = 9538
SERVER = f"http://{HOST}:{WEB_PORT}"
DRIVER = f"http://{HOST}:{DRIVER_PORT}"
REFERENCE = "reference/v1.2/crystal-icons.html"
CONTRACT = ROOT / "contracts/v1.2/crystal-icons.candidate.json"
TOKENS = ROOT / "tokens/glaze-v1.2-crystal-icons.candidate.json"
CSS = ROOT / "css/glaze-v1.2-crystal-icons.candidate.css"
ENTRYPOINT = ROOT / "css/glaze-v1.2.0-candidate.css"
EXPECTED_SIZES = [16, 20, 24, 28, 32]
EXPECTED_STROKES = [2.4, 2.2, 2.0, 1.85, 1.7]

class AcceptanceError(RuntimeError):
    pass

def require(ok: bool, message: str) -> None:
    if not ok:
        raise AcceptanceError(message)

def validate_source() -> None:
    for path in (CONTRACT, TOKENS, CSS, ENTRYPOINT, ROOT / REFERENCE):
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    tokens = json.loads(TOKENS.read_text(encoding="utf-8"))
    require(contract.get("version") == "1.2.0-candidate", "Crystal contract version drifted")
    require(contract.get("lifecycle") == "candidate" and contract.get("consumerEligible") is False, "Crystal lifecycle boundary drifted")
    require(contract.get("stableBaseline") == "1.1.0", "Stable baseline drifted")
    require(set(contract.get("presentationFamilies", {})) == {"outline", "filled", "dimensional"}, "Crystal presentation families drifted")
    sizes = contract.get("opticalSizes", {})
    require([int(k) for k in sizes if k.isdigit()] == EXPECTED_SIZES, "Crystal optical-size set drifted")
    require([float(sizes[str(k)]["strokeViewBox"]) for k in EXPECTED_SIZES] == EXPECTED_STROKES, "Crystal optical stroke map drifted")
    require(contract.get("state", {}).get("selectionMayNotRelyOnlyOnBlue") is True, "selection non-color rule drifted")
    require(contract.get("state", {}).get("selectedMustRemainRecognizableInMonochrome") is True, "monochrome selected-state rule drifted")
    require(contract.get("motion", {}).get("reducedMotionAlternativeRequired") is True, "Reduced Motion rule drifted")
    require(contract.get("accessibility", {}).get("interactiveAccessibleNameRequired") is True, "accessible-name rule drifted")
    impl = contract.get("implementation", {})
    require(impl.get("tokens") == "tokens/glaze-v1.2-crystal-icons.candidate.json", "Crystal token binding drifted")
    require(impl.get("webLayer") == "css/glaze-v1.2-crystal-icons.candidate.css", "Crystal CSS binding drifted")
    require(impl.get("reference") == REFERENCE, "Crystal reference binding drifted")
    require(impl.get("renderedValidator") == "scripts/validate_glaze_v1_2_crystal_icons_rendered.py", "Crystal validator binding drifted")
    require(tokens.get("version") == "1.2.0-candidate" and tokens.get("consumerEligible") is False, "Crystal tokens lifecycle drifted")
    require([tokens.get("sizes", {}).get(k) for k in ("dense", "compact", "standard", "prominent", "navigation")] == EXPECTED_SIZES, "Crystal size tokens drifted")
    require([float(tokens.get("strokeViewBox", {}).get(str(k), -1)) for k in EXPECTED_SIZES] == EXPECTED_STROKES, "Crystal stroke tokens drifted")
    require(tokens.get("rules", {}).get("selectionBlueOnly") is False, "Crystal selection token rule drifted")
    text = (CSS.read_text(encoding="utf-8") + "\n" + (ROOT / REFERENCE).read_text(encoding="utf-8")).lower()
    for marker in ("data-glz-icon-family=\"outline\"", "data-glz-icon-family=\"filled\"", "data-glz-icon-family=\"dimensional\"", "data-glz-icon-size=\"16\"", "data-glz-icon-size=\"32\"", "prefers-reduced-motion: reduce", "forced-colors: active", "data-state=\"selected\""):
        require(marker in text, f"Crystal implementation marker missing: {marker}")
    for forbidden in ("unpkg.com", "cdnjs.cloudflare.com", "jsdelivr.net", "fonts.googleapis.com", "<img src=\"http", "<script src=\"http"):
        require(forbidden not in text, f"external runtime icon dependency found: {forbidden}")
    entry = ENTRYPOINT.read_text(encoding="utf-8")
    chain = [
        '@import url("./glaze-v1.2-chrome-optics.candidate.css")',
        '@import url("./glaze-v1.2-crystal-icons.candidate.css")',
        '@import url("./glaze-v1.2-legacy-aura-retirement.candidate.css")',
        '@import url("./glaze-v1.2-typography.candidate.css")',
        '@import url("./glaze-v1.2-accessibility.candidate.css")',
    ]
    require(all(item in entry for item in chain), "Candidate entrypoint missing Crystal import chain")
    indexes = [entry.index(item) for item in chain]
    require(indexes == sorted(indexes), "Crystal/accessibility import order drifted")

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
    value = request("POST", "/session", {"capabilities": {"alwaysMatch": {"browserName": "chrome", "goog:chromeOptions": {"args": ["--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-background-networking", "--disable-component-update", "--disable-extensions", "--disable-sync", "--metrics-recording-only", "--no-first-run", "--window-size=1280,960"]}}}}, timeout=60)
    require(isinstance(value, dict) and isinstance(value.get("sessionId"), str), "Chrome returned no session id")
    return value["sessionId"]

def execute(sid: str, script: str) -> Any:
    return request("POST", f"/session/{sid}/execute/sync", {"script": script, "args": []})

def cdp(sid: str, cmd: str, params: dict[str, Any] | None = None) -> Any:
    return request("POST", f"/session/{sid}/goog/cdp/execute", {"cmd": cmd, "params": params or {}})

def viewport(sid: str, width: int, height: int, mobile: bool = False) -> None:
    cdp(sid, "Emulation.setDeviceMetricsOverride", {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": mobile, "screenWidth": width, "screenHeight": height})

def media(sid: str, features: list[dict[str, str]]) -> None:
    cdp(sid, "Emulation.setEmulatedMedia", {"media": "screen", "features": features})

def navigate(sid: str) -> None:
    request("POST", f"/session/{sid}/url", {"url": f"{SERVER}/{REFERENCE}"})
    end = time.monotonic() + 15
    while time.monotonic() < end:
        if execute(sid, "return document.readyState") == "complete":
            return
        time.sleep(.1)
    raise AcceptanceError("Crystal reference did not finish loading")

def screenshot(sid: str, name: str) -> None:
    encoded = request("GET", f"/session/{sid}/screenshot")
    require(isinstance(encoded, str) and encoded, "no screenshot bytes")
    ARTIFACTS.mkdir(exist_ok=True)
    path = ARTIFACTS / f"glaze-v1.2-crystal-icons-{name}.png"
    path.write_bytes(base64.b64decode(encoded))
    require(path.stat().st_size > 7000, f"invalid screenshot {path}")

STATE_JS = r"""
const root=document.documentElement;
const ladder=[...document.querySelectorAll('#size-ladder .glz12-crystal-icon')].map(svg=>{const c=getComputedStyle(svg),g=getComputedStyle(svg.children[0]);return {size:parseFloat(c.width),height:parseFloat(c.height),stroke:parseFloat(g.strokeWidth),fill:g.fill,strokeColor:g.stroke}});
const fam=[...document.querySelectorAll('.family-card .glz12-crystal-icon')].map(svg=>{const c=getComputedStyle(svg),g=getComputedStyle(svg.children[0]),b=svg.getBBox();return {family:svg.dataset.glzIconFamily,size:parseFloat(c.width),fill:g.fill,stroke:g.stroke,filter:c.filter,bbox:{x:b.x,y:b.y,w:b.width,h:b.height}}});
const buttons=[...document.querySelectorAll('.glz12-icon-control')];
const def=buttons.find(x=>x.dataset.state==='default'), sel=buttons.find(x=>x.dataset.state==='selected');
const dsvg=def.querySelector('.glz12-crystal-icon'), ssvg=sel.querySelector('.glz12-crystal-icon'), dc=getComputedStyle(def), sc=getComputedStyle(sel), dg=getComputedStyle(dsvg.children[0]), sg=getComputedStyle(ssvg.children[0]), after=getComputedStyle(sel,'::after');
const sync=document.querySelector('[data-icon-name="sync"]'), syncStyle=getComputedStyle(sync);
return {ready:document.readyState,width:innerWidth,scrollWidth:document.documentElement.scrollWidth,version:root.dataset.glazeVersion,upgrade:root.dataset.glazeUpgrade,appearance:root.dataset.glzAppearance,mode:root.dataset.glzIconMode||'',ladder,fam,state:{defaultBorder:parseFloat(dc.borderTopWidth),selectedBorder:parseFloat(sc.borderTopWidth),defaultFill:dg.fill,defaultStroke:dg.stroke,selectedFill:sg.fill,selectedStroke:sg.stroke,selectedAfterContent:after.content,selectedAfterHeight:parseFloat(after.height),selectedAfterWidth:parseFloat(after.width),selectedAfterBackground:after.backgroundColor,selectedBackground:sc.backgroundColor},sync:{animationName:syncStyle.animationName,animationDuration:syncStyle.animationDuration},names:buttons.map(b=>b.getAttribute('aria-label')),targets:buttons.map(b=>({w:b.getBoundingClientRect().width,h:b.getBoundingClientRect().height}))};
"""

def state(sid: str) -> dict[str, Any]:
    value = execute(sid, STATE_JS)
    require(isinstance(value, dict), f"could not read Crystal state: {value!r}")
    return value

def validate_state(s: dict[str, Any], width: int) -> None:
    require(s.get("ready") == "complete" and abs(int(s.get("width", 0)) - width) <= 1, f"page/viewport mismatch: {s}")
    require(int(s.get("scrollWidth", width + 2)) <= width + 1, f"horizontal overflow: {s}")
    require(s.get("version") == "1.1" and s.get("upgrade") == "v1.2-frosted-neutral", "Candidate activation boundary missing")
    ladder = s.get("ladder", [])
    require([round(x.get("size", -1)) for x in ladder] == EXPECTED_SIZES, f"Crystal rendered size ladder drifted: {ladder}")
    require(all(abs(x.get("size", 0)-x.get("height", 1)) < .2 for x in ladder), f"Crystal icons are not square: {ladder}")
    strokes = [round(float(x.get("stroke", -1)), 2) for x in ladder]
    require(strokes == EXPECTED_STROKES, f"Crystal rendered stroke ladder drifted: {strokes}")
    require(all(strokes[i] > strokes[i+1] for i in range(len(strokes)-1)), f"smaller optical sizes must use heavier relative strokes: {strokes}")
    fam = {x.get("family"): x for x in s.get("fam", [])}
    require(set(fam) == {"outline", "filled", "dimensional"}, f"Crystal rendered families drifted: {fam}")
    require(fam["outline"]["fill"] == "none" and fam["outline"]["stroke"] != "none", f"outline family drifted: {fam['outline']}")
    require(fam["filled"]["fill"] != "none" and fam["filled"]["stroke"] == "none", f"filled family drifted: {fam['filled']}")
    for key in ("x", "y", "w", "h"):
        require(abs(float(fam["outline"]["bbox"][key])-float(fam["filled"]["bbox"][key])) < .05, f"outline/filled geometry diverged at {key}: {fam}")
    st = s.get("state", {})
    require(abs(float(st.get("defaultBorder", 0))-1) < .1 and abs(float(st.get("selectedBorder", 0))-2) < .1, f"structural selected border drifted: {st}")
    require(st.get("defaultFill") == "none" and st.get("defaultStroke") != "none", f"default outline state drifted: {st}")
    require(st.get("selectedFill") != "none" and st.get("selectedStroke") == "none", f"selected filled geometry drifted: {st}")
    require(st.get("selectedAfterContent") not in (None, "none", "normal"), f"selected physical indicator missing: {st}")
    require(1.5 <= float(st.get("selectedAfterHeight", 0)) <= 2.5, f"selected indicator thickness drifted: {st}")
    require(float(st.get("selectedAfterWidth", 0)) >= 8, f"selected indicator width drifted: {st}")
    require(st.get("selectedAfterBackground") not in (None, "", "transparent", "rgba(0, 0, 0, 0)"), f"selected indicator lost visible paint: {st}")
    require(all(isinstance(name, str) and name.strip() for name in s.get("names", [])), f"interactive Crystal icons missing accessible names: {s.get('names')}")
    require(all(float(t.get("w", 0)) >= 48 and float(t.get("h", 0)) >= 48 for t in s.get("targets", [])), f"Crystal icon controls violate 48 px target floor: {s.get('targets')}")

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
        viewport(sid, 1280, 960)
        media(sid, [])
        navigate(sid)
        for appearance in ("light", "dark", "deep-dark"):
            execute(sid, f"document.documentElement.setAttribute('data-glz-appearance','{appearance}');document.documentElement.removeAttribute('data-glz-icon-mode');return true;")
            s = state(sid)
            validate_state(s, 1280)
            require(s.get("sync", {}).get("animationName") == "glz12-crystal-activity-spin", f"meaningful activity motion missing: {s.get('sync')}")
            screenshot(sid, appearance)
        execute(sid, "document.documentElement.setAttribute('data-glz-icon-mode','monochrome');return true;")
        mono = state(sid)
        validate_state(mono, 1280)
        require(abs(float(mono["state"]["selectedBorder"])-2) < .1 and mono["state"]["selectedFill"] != "none", f"monochrome selected state lost structural meaning: {mono['state']}")
        screenshot(sid, "monochrome")
        media(sid, [{"name": "prefers-reduced-motion", "value": "reduce"}])
        reduced = state(sid)
        validate_state(reduced, 1280)
        require(reduced.get("sync", {}).get("animationName") == "none", f"Reduced Motion did not disable activity animation: {reduced.get('sync')}")
        screenshot(sid, "reduced-motion")
        media(sid, [{"name": "forced-colors", "value": "active"}])
        forced = state(sid)
        validate_state(forced, 1280)
        require(forced["state"]["selectedFill"] != "none" and abs(float(forced["state"]["selectedBorder"])-2) < .1, f"Forced Colors lost structural selected state: {forced['state']}")
        require(forced.get("sync", {}).get("animationName") == "none", f"Forced Colors should suppress decorative/activity motion in reference: {forced.get('sync')}")
        screenshot(sid, "forced-colors")
        media(sid, [])
        execute(sid, "document.documentElement.removeAttribute('data-glz-icon-mode');document.documentElement.style.fontSize='200%';document.documentElement.setAttribute('data-glz-appearance','light');return true;")
        viewport(sid, 390, 844, True)
        large = state(sid)
        require(int(large.get("scrollWidth", 392)) <= 391, f"200% mobile Crystal scene overflow: {large}")
        require(all(float(t.get("w", 0)) >= 48 and float(t.get("h", 0)) >= 48 for t in large.get("targets", [])), f"200% mobile target floor drifted: {large.get('targets')}")
        screenshot(sid, "mobile-200-percent")
        print("GLAZE UI V1.2 Crystal Icon System rendered validation passed.")
        return 0
    except Exception as error:
        print(f"GLAZE UI V1.2 Crystal Icon System rendered validation failed: {error}", file=sys.stderr)
        return 1
    finally:
        if sid:
            try:
                request("DELETE", f"/session/{sid}")
            except Exception:
                pass
        for process in (driver, http):
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()

if __name__ == "__main__":
    raise SystemExit(main())

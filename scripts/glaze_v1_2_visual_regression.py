#!/usr/bin/env python3
"""Deterministic V1.2 Candidate screenshot capture and provisional pixel-drift comparison."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import shutil
import struct
import subprocess
import sys
import time
import zlib
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = SCRIPT_ROOT / "contracts/v1.2/visual-regression.candidate.json"
HOST = "127.0.0.1"
WEB_PORT = 8812
DRIVER_PORT = 9562
SERVER = f"http://{HOST}:{WEB_PORT}"
DRIVER = f"http://{HOST}:{DRIVER_PORT}"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class RegressionError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RegressionError(message)


def load_contract() -> dict[str, Any]:
    require(CONTRACT_PATH.is_file(), f"missing {CONTRACT_PATH.relative_to(SCRIPT_ROOT)}")
    value = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "visual regression contract must be an object")
    return value


def request(method: str, path: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> Any:
    req = Request(
        f"{DRIVER}{path}",
        data=None if payload is None else json.dumps(payload).encode("utf-8"),
        method=method,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as error:
        raise RegressionError(f"WebDriver HTTP {error.code}: {error.read().decode(errors='replace')}") from error
    except (URLError, TimeoutError) as error:
        raise RegressionError(f"WebDriver request failed: {error}") from error
    if not raw:
        return None
    value = json.loads(raw.decode("utf-8")).get("value")
    if isinstance(value, dict) and value.get("error"):
        raise RegressionError(f"WebDriver {value.get('error')}: {value.get('message', '')}")
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
    raise RegressionError(f"HTTP endpoint not ready: {last}")


def chromedriver() -> str:
    for item in (shutil.which("chromedriver"), "/usr/bin/chromedriver", "/usr/local/share/chromedriver-linux64/chromedriver"):
        if item and Path(item).is_file():
            return str(item)
    raise RegressionError("chromedriver unavailable")


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
    raise RegressionError(f"chromedriver not ready: {last}")


def create_session() -> str:
    value = request(
        "POST",
        "/session",
        {"capabilities": {"alwaysMatch": {
            "browserName": "chrome",
            "goog:chromeOptions": {"args": [
                "--headless=new",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-background-networking",
                "--disable-component-update",
                "--disable-default-apps",
                "--disable-extensions",
                "--disable-sync",
                "--metrics-recording-only",
                "--no-first-run",
                "--hide-scrollbars",
                "--window-size=1440,1200",
            ]},
        }}},
        timeout=60,
    )
    require(isinstance(value, dict) and isinstance(value.get("sessionId"), str), "Chrome returned no session id")
    return value["sessionId"]


def execute(sid: str, script: str) -> Any:
    return request("POST", f"/session/{sid}/execute/sync", {"script": script, "args": []})


def cdp(sid: str, command: str, params: dict[str, Any] | None = None) -> Any:
    return request("POST", f"/session/{sid}/goog/cdp/execute", {"cmd": command, "params": params or {}})


def set_viewport(sid: str, width: int, height: int, mobile: bool) -> None:
    cdp(sid, "Emulation.setDeviceMetricsOverride", {
        "width": width,
        "height": height,
        "deviceScaleFactor": 1,
        "mobile": mobile,
        "screenWidth": width,
        "screenHeight": height,
    })
    cdp(sid, "Emulation.setTouchEmulationEnabled", {"enabled": mobile, "maxTouchPoints": 5 if mobile else 1})


def set_media(sid: str, features: list[dict[str, str]]) -> None:
    cdp(sid, "Emulation.setEmulatedMedia", {"media": "screen", "features": features})


def wait_ready(sid: str, expression: str, seconds: float = 15) -> None:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        value = execute(sid, f"return document.readyState === 'complete' && ({expression});")
        if value is True:
            return
        time.sleep(.1)
    raise RegressionError(f"reference did not become ready: {expression}")


def prepare_scene(sid: str, scene: dict[str, Any]) -> None:
    attrs = scene.get("htmlAttributes", {})
    style = scene.get("rootStyle", {})
    isolate = scene.get("isolate")
    payload = json.dumps({"attrs": attrs, "style": style, "isolate": isolate})
    result = execute(sid, f"""
const cfg={payload};
const root=document.documentElement;
for(const [name,value] of Object.entries(cfg.attrs||{{}})) root.setAttribute(name,String(value));
for(const [name,value] of Object.entries(cfg.style||{{}})) root.style.setProperty(name,String(value));
if(cfg.isolate){{
  const target=document.querySelector(cfg.isolate.targetSelector);
  if(!target) return {{error:'missing isolate target'}};
  for(const node of document.querySelectorAll(cfg.isolate.allSelector)) node.hidden=node!==target;
  for(const selector of (cfg.isolate.hideSelectors||[])) for(const node of document.querySelectorAll(selector)) node.hidden=true;
}}
let freeze=document.getElementById('glz12-visual-regression-freeze');
if(!freeze){{
  freeze=document.createElement('style');
  freeze.id='glz12-visual-regression-freeze';
  freeze.textContent='*,*::before,*::after{{animation:none!important;transition:none!important;caret-color:transparent!important;scroll-behavior:auto!important}}';
  document.head.appendChild(freeze);
}}
window.scrollTo(0,0);
return {{error:null}};
""")
    require(isinstance(result, dict) and result.get("error") is None, f"scene preparation failed: {result}")
    end = time.monotonic() + 10
    while time.monotonic() < end:
        fonts = execute(sid, "return !document.fonts || document.fonts.status === 'loaded';")
        if fonts is True:
            break
        time.sleep(.1)
    else:
        raise RegressionError("fonts did not become ready")
    time.sleep(.15)


def screenshot(sid: str, path: Path) -> None:
    encoded = request("GET", f"/session/{sid}/screenshot")
    require(isinstance(encoded, str) and encoded, f"no screenshot bytes for {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(base64.b64decode(encoded))
    require(path.stat().st_size > 5000, f"invalid screenshot {path}")


def git_revision(root: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except Exception as error:
        raise RegressionError(f"could not resolve revision for {root}: {error}") from error


def capture(root: Path, output: Path) -> dict[str, Any]:
    contract = load_contract()
    scenes = contract.get("scenes", [])
    require(isinstance(scenes, list) and scenes, "visual regression scene list missing")
    root = root.resolve()
    output = output.resolve()
    require(root.is_dir(), f"capture root missing: {root}")
    for scene in scenes:
        require((root / scene["page"]).is_file(), f"capture root missing page: {scene['page']}")

    http = driver = None
    sid: str | None = None
    captured: list[dict[str, Any]] = []
    try:
        http = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(WEB_PORT), "--bind", HOST, "--directory", str(root)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        first_page = str(scenes[0]["page"])
        wait_http(f"{SERVER}/{first_page}")
        driver = subprocess.Popen(
            [chromedriver(), f"--port={DRIVER_PORT}", "--allowed-ips=127.0.0.1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        wait_driver()
        sid = create_session()
        for scene in scenes:
            scene_id = str(scene["id"])
            width, height = [int(x) for x in scene["viewport"]]
            set_viewport(sid, width, height, bool(scene.get("mobile", False)))
            set_media(sid, list(scene.get("mediaFeatures", [])))
            request("POST", f"/session/{sid}/url", {"url": f"{SERVER}/{scene['page']}"})
            wait_ready(sid, str(scene.get("readyExpression", "true")))
            prepare_scene(sid, scene)
            dimensions = execute(sid, "return [innerWidth,innerHeight,document.documentElement.scrollWidth];")
            require(isinstance(dimensions, list) and abs(int(dimensions[0]) - width) <= 1 and abs(int(dimensions[1]) - height) <= 1, f"viewport drift for {scene_id}: {dimensions}")
            require(int(dimensions[2]) <= width + 1, f"horizontal overflow for {scene_id}: {dimensions}")
            path = output / f"{scene_id}.png"
            screenshot(sid, path)
            captured.append({"id": scene_id, "path": str(path), "viewport": [width, height], "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        return {"revision": git_revision(root), "count": len(captured), "captures": captured}
    finally:
        if sid:
            try:
                request("DELETE", f"/session/{sid}", timeout=5)
            except Exception:
                pass
        for process in (driver, http):
            if process:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()


def paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def decode_png(path: Path) -> tuple[int, int, bytes]:
    data = path.read_bytes()
    require(data.startswith(PNG_SIGNATURE), f"not a PNG: {path}")
    offset = len(PNG_SIGNATURE)
    width = height = bit_depth = color_type = interlace = None
    compressed = bytearray()
    while offset < len(data):
        require(offset + 12 <= len(data), f"truncated PNG chunk: {path}")
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        offset += 12 + length
        if kind == b"IHDR":
            width, height, bit_depth, color_type, _compression, _filter, interlace = struct.unpack(">IIBBBBB", payload)
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            break
    require(all(x is not None for x in (width, height, bit_depth, color_type, interlace)), f"missing PNG IHDR: {path}")
    require(bit_depth == 8 and interlace == 0, f"unsupported PNG format in {path}: depth={bit_depth} interlace={interlace}")
    channels = {0: 1, 2: 3, 4: 2, 6: 4}.get(int(color_type))
    require(channels is not None, f"unsupported PNG color type {color_type}: {path}")
    stride = int(width) * int(channels)
    raw = zlib.decompress(bytes(compressed))
    require(len(raw) == (stride + 1) * int(height), f"unexpected PNG scanline size: {path}")
    previous = bytearray(stride)
    pixels = bytearray()
    cursor = 0
    for _row in range(int(height)):
        filter_type = raw[cursor]
        cursor += 1
        encoded = raw[cursor:cursor + stride]
        cursor += stride
        row = bytearray(stride)
        for i, value in enumerate(encoded):
            left = row[i - channels] if i >= channels else 0
            up = previous[i]
            upper_left = previous[i - channels] if i >= channels else 0
            if filter_type == 0:
                recon = value
            elif filter_type == 1:
                recon = (value + left) & 255
            elif filter_type == 2:
                recon = (value + up) & 255
            elif filter_type == 3:
                recon = (value + ((left + up) // 2)) & 255
            elif filter_type == 4:
                recon = (value + paeth(left, up, upper_left)) & 255
            else:
                raise RegressionError(f"unsupported PNG filter {filter_type}: {path}")
            row[i] = recon
        previous = row
        if color_type == 6:
            pixels.extend(row)
        elif color_type == 2:
            for i in range(0, len(row), 3):
                pixels.extend((row[i], row[i + 1], row[i + 2], 255))
        elif color_type == 4:
            for i in range(0, len(row), 2):
                pixels.extend((row[i], row[i], row[i], row[i + 1]))
        else:
            for value in row:
                pixels.extend((value, value, value, 255))
    return int(width), int(height), bytes(pixels)


def compare_dirs(baseline: Path, current: Path, baseline_root: Path, current_root: Path, evidence: Path) -> dict[str, Any]:
    contract = load_contract()
    expected = [f"{scene['id']}.png" for scene in contract.get("scenes", [])]
    require(expected, "visual regression scene list missing")
    require(sorted(p.name for p in baseline.glob("*.png")) == sorted(expected), "baseline screenshot set drifted")
    require(sorted(p.name for p in current.glob("*.png")) == sorted(expected), "current screenshot set drifted")
    expected_reference = str(contract.get("provisionalReference", {}).get("revision", ""))
    actual_reference = git_revision(baseline_root.resolve())
    current_revision = git_revision(current_root.resolve())
    require(actual_reference == expected_reference, f"provisional reference checkout drifted: expected {expected_reference}, got {actual_reference}")

    changed_tolerance = int(contract.get("comparison", {}).get("changedPixelTolerance", -1))
    channel_tolerance = int(contract.get("comparison", {}).get("maximumChannelDeltaTolerance", -1))
    require(changed_tolerance == 0 and channel_tolerance == 0, "first V1.2 provisional gate must remain zero-drift")
    comparisons: list[dict[str, Any]] = []
    failures: list[str] = []
    for name in expected:
        base_path, cur_path = baseline / name, current / name
        bw, bh, bp = decode_png(base_path)
        cw, ch, cp = decode_png(cur_path)
        require((bw, bh) == (cw, ch), f"dimension drift for {name}: {(bw, bh)} != {(cw, ch)}")
        changed = 0
        maximum = 0
        for i in range(0, len(bp), 4):
            delta = max(abs(bp[i + c] - cp[i + c]) for c in range(4))
            if delta:
                changed += 1
                maximum = max(maximum, delta)
        total = bw * bh
        item = {
            "name": name,
            "dimensions": [bw, bh],
            "totalPixels": total,
            "changedPixels": changed,
            "changedPixelPercent": (changed * 100.0 / total) if total else 0.0,
            "maximumChannelDelta": maximum,
            "baselineSha256": hashlib.sha256(base_path.read_bytes()).hexdigest(),
            "currentSha256": hashlib.sha256(cur_path.read_bytes()).hexdigest(),
        }
        comparisons.append(item)
        if changed > changed_tolerance or maximum > channel_tolerance:
            failures.append(f"{name}: {changed} changed pixels, max channel delta {maximum}")

    result = {
        "status": "failed" if failures else "passed",
        "comparisonMode": contract.get("comparison", {}).get("mode"),
        "provisionalReferenceRevision": actual_reference,
        "currentRevision": current_revision,
        "humanApprovedBaseline": contract.get("provisionalReference", {}).get("humanApproved"),
        "acceptanceAuthority": contract.get("provisionalReference", {}).get("acceptanceAuthority"),
        "sceneCount": len(comparisons),
        "comparisons": comparisons,
        "failures": failures,
        "boundary": "Provisional same-environment zero-drift evidence only; human optical review and final acceptable-difference thresholds remain separate.",
    }
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(not failures, "visual regression drift detected: " + "; ".join(failures))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    cap = sub.add_parser("capture")
    cap.add_argument("--root", required=True)
    cap.add_argument("--out", required=True)
    cmp = sub.add_parser("compare")
    cmp.add_argument("--baseline", required=True)
    cmp.add_argument("--current", required=True)
    cmp.add_argument("--baseline-root", required=True)
    cmp.add_argument("--current-root", required=True)
    cmp.add_argument("--evidence", required=True)
    args = parser.parse_args()
    try:
        if args.command == "capture":
            result = capture(Path(args.root), Path(args.out))
            print(json.dumps(result, indent=2))
        else:
            result = compare_dirs(Path(args.baseline), Path(args.current), Path(args.baseline_root), Path(args.current_root), Path(args.evidence))
            print(f"PASS: compared {result['sceneCount']} stabilized V1.2 screenshots with zero decoded-pixel drift.")
        return 0
    except (RegressionError, OSError, json.JSONDecodeError, zlib.error) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

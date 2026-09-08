#!/usr/bin/env python3
"""Capture V1.2 provisional baseline/current scenes in one stabilized browser session.

This helper strengthens the existing zero-drift visual-regression gate. It does not
add perceptual tolerance: every accepted baseline/current decoded pixel must still
match exactly. The pair is rendered by one Chrome session, and each scene must
produce two consecutive identical decoded frames before it is retained.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = ROOT / "scripts/glaze_v1_2_visual_regression.py"
BASELINE_PORT = 8812
CURRENT_PORT = 8813
HOST = "127.0.0.1"


def load_harness():
    spec = importlib.util.spec_from_file_location("glaze_v1_2_visual_regression", HARNESS_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load V1.2 visual-regression harness")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


h = load_harness()


def stable_screenshot(sid: str, path: Path, attempts: int = 6) -> dict[str, Any]:
    """Require two consecutive byte-decoded frames to agree exactly."""
    path.parent.mkdir(parents=True, exist_ok=True)
    previous: tuple[int, int, bytes] | None = None
    previous_raw: bytes | None = None
    stable_attempt = 0

    for attempt in range(1, attempts + 1):
        encoded = h.request("GET", f"/session/{sid}/screenshot")
        h.require(isinstance(encoded, str) and encoded, f"no screenshot bytes for {path.name}")
        raw = base64.b64decode(encoded)
        h.require(len(raw) > 5000, f"invalid screenshot {path}")

        probe = path.parent / f".{path.name}.stability-{attempt}.png"
        probe.write_bytes(raw)
        try:
            decoded = h.decode_png(probe)
        finally:
            probe.unlink(missing_ok=True)

        if previous is not None and decoded == previous:
            path.write_bytes(raw)
            stable_attempt = attempt
            break

        previous = decoded
        previous_raw = raw
        # Give the compositor another completed frame without accepting a timed
        # guess as evidence. Exact repeated decoded pixels are the authority.
        h.execute(sid, "document.documentElement.getBoundingClientRect(); return true;")
        time.sleep(0.10)
    else:
        if previous_raw is not None:
            (path.parent / f"{path.stem}.unstable-last.png").write_bytes(previous_raw)
        raise h.RegressionError(
            f"scene did not reach exact repeated-frame decoded-pixel stability: {path.name}"
        )

    return {
        "path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "stableOnAttempt": stable_attempt,
    }


def start_server(root: Path, port: int) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "http.server",
            str(port),
            "--bind",
            HOST,
            "--directory",
            str(root),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def capture_target(
    sid: str,
    root: Path,
    server: str,
    output: Path,
    scenes: list[dict[str, Any]],
) -> dict[str, Any]:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)

    captures: list[dict[str, Any]] = []
    for scene in scenes:
        scene_id = str(scene["id"])
        width, height = [int(x) for x in scene["viewport"]]
        h.set_viewport(sid, width, height, bool(scene.get("mobile", False)))
        h.set_media(sid, list(scene.get("mediaFeatures", [])))
        h.request("POST", f"/session/{sid}/url", {"url": f"{server}/{scene['page']}"})
        h.wait_ready(sid, str(scene.get("readyExpression", "true")))
        h.prepare_scene(sid, scene)

        dimensions = h.execute(
            sid,
            "return [innerWidth,innerHeight,document.documentElement.scrollWidth,devicePixelRatio];",
        )
        h.require(
            isinstance(dimensions, list)
            and abs(int(dimensions[0]) - width) <= 1
            and abs(int(dimensions[1]) - height) <= 1,
            f"viewport drift for {scene_id}: {dimensions}",
        )
        h.require(int(dimensions[2]) <= width + 1, f"horizontal overflow for {scene_id}: {dimensions}")
        h.require(float(dimensions[3]) == 1.0, f"device-pixel-ratio drift for {scene_id}: {dimensions}")

        path = output / f"{scene_id}.png"
        item = stable_screenshot(sid, path)
        item.update({"id": scene_id, "viewport": [width, height]})
        captures.append(item)

    return {
        "revision": h.git_revision(root),
        "count": len(captures),
        "captures": captures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-root", required=True)
    parser.add_argument("--current-root", required=True)
    parser.add_argument("--baseline-out", required=True)
    parser.add_argument("--current-out", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    baseline_root = Path(args.baseline_root).resolve()
    current_root = Path(args.current_root).resolve()
    baseline_out = Path(args.baseline_out).resolve()
    current_out = Path(args.current_out).resolve()
    manifest_path = Path(args.manifest).resolve()

    contract = h.load_contract()
    scenes = contract.get("scenes", [])
    h.require(isinstance(scenes, list) and scenes, "visual regression scene list missing")
    for root in (baseline_root, current_root):
        h.require(root.is_dir(), f"capture root missing: {root}")
        for scene in scenes:
            h.require((root / scene["page"]).is_file(), f"capture root missing page: {scene['page']}")

    baseline_http = current_http = driver = None
    sid: str | None = None
    try:
        baseline_http = start_server(baseline_root, BASELINE_PORT)
        current_http = start_server(current_root, CURRENT_PORT)
        baseline_server = f"http://{HOST}:{BASELINE_PORT}"
        current_server = f"http://{HOST}:{CURRENT_PORT}"
        h.wait_http(f"{baseline_server}/{scenes[0]['page']}")
        h.wait_http(f"{current_server}/{scenes[0]['page']}")

        driver = subprocess.Popen(
            [h.chromedriver(), f"--port={h.DRIVER_PORT}", "--allowed-ips=127.0.0.1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        h.wait_driver()
        sid = h.create_session()

        baseline = capture_target(sid, baseline_root, baseline_server, baseline_out, scenes)
        current = capture_target(sid, current_root, current_server, current_out, scenes)

        manifest = {
            "captureMode": "same-browser-session-exact-repeated-frame",
            "decodedPixelToleranceIntroduced": False,
            "baseline": baseline,
            "current": current,
        }
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(manifest, indent=2))
        return 0
    except h.RegressionError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    finally:
        if sid:
            try:
                h.request("DELETE", f"/session/{sid}", timeout=5)
            except Exception:
                pass
        for process in (driver, current_http, baseline_http):
            if process:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()


if __name__ == "__main__":
    raise SystemExit(main())

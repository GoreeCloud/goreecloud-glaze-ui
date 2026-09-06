#!/usr/bin/env python3
"""Run frozen V1.2 Candidate-era validators under V1.2 Stable authority.

GLAZE UI V1.2 Stable intentionally promoted the already-qualified Candidate
source layer without renaming every Candidate-suffixed source file. Several
pre-promotion validators contain valuable deep source assertions but also encode
the historical global lifecycle state (V1.1 current Stable / V1.2 active
Candidate). This runner keeps those validators unchanged as historical-source
checks while validating the real Stable lifecycle first.

The historical VERSION/lifecycle projection is ephemeral, exists only inside the
checkout, and is never committed or represented as release/qualification
evidence.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE_VERSION = ROOT / "VERSION"
LIVE_LIFECYCLE = ROOT / "registry/lifecycle.json"


def req(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"GLAZE UI V1.2 promoted-source compatibility failed: {message}")


def load_json(path: Path) -> dict:
    req(path.is_file(), f"missing required file: {path.relative_to(ROOT)}")
    value = json.loads(path.read_text(encoding="utf-8"))
    req(isinstance(value, dict), f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def validate_live_stable() -> dict:
    version = LIVE_VERSION.read_text(encoding="utf-8").strip()
    lifecycle = load_json(LIVE_LIFECYCLE)
    req(version == "1.2.0", "live VERSION must remain 1.2.0")
    req(lifecycle.get("officialProductLabel") == "GLAZE UI V1.2", "live product label drifted")
    req(lifecycle.get("currentStable") == "1.2.0", "live currentStable must remain 1.2.0")
    req(lifecycle.get("currentOfficial") == "1.2.0", "live currentOfficial must remain 1.2.0")
    req(lifecycle.get("activeCandidate") is None, "V1.2 Stable must not regain an active V1.2 Candidate")
    req(lifecycle.get("plannedNext") == "1.3.0-candidate", "plannedNext must remain V1.3 Candidate")
    stable = next(
        (item for item in lifecycle.get("releases", []) if isinstance(item, dict) and item.get("version") == "1.2.0"),
        None,
    )
    req(stable is not None, "live V1.2 Stable release record is missing")
    assert stable is not None
    req(stable.get("status") == "stable", "live V1.2 release must remain Stable")
    req(stable.get("consumerEligible") is True, "live V1.2 Stable must remain consumer-eligible")
    req(stable.get("stableBaseline") == "1.1.0", "V1.2 rollback baseline must remain 1.1.0")
    return lifecycle


def historical_projection(live: dict) -> dict:
    projected = copy.deepcopy(live)
    projected["officialProductLabel"] = "GLAZE UI V1.1"
    projected["currentStable"] = "1.1.0"
    projected["currentOfficial"] = "1.1.0"
    projected["activeCandidate"] = "1.2.0-candidate"

    stable_v12 = next(
        (item for item in projected.get("releases", []) if isinstance(item, dict) and item.get("version") == "1.2.0"),
        {},
    )
    candidate = copy.deepcopy(stable_v12)
    candidate.update(
        {
            "version": "1.2.0-candidate",
            "label": "GLAZE UI V1.2 — Frosted Neutral Candidate",
            "status": "candidate",
            "consumerEligible": False,
            "stableBaseline": "1.1.0",
            "contract": "GLAZE_UI_V1_2_CANDIDATE.md",
            "opticalFoundation": "tokens/glaze-v1.2-optical-foundation.candidate.json",
            "migration": "contracts/v1.2/migration.candidate.json",
            "promotionGates": "acceptance/v1.2-promotion-gates.candidate.md",
            "webEntrypoint": "css/glaze-v1.2.0-candidate.css",
        }
    )
    releases = [
        item
        for item in projected.get("releases", [])
        if not (isinstance(item, dict) and item.get("version") == "1.2.0-candidate")
    ]
    releases.append(candidate)
    projected["releases"] = releases

    shell = copy.deepcopy(projected.get("capabilities", {}).get("frosted-neutral-system-shell", {}))
    shell.update(
        {
            "status": "candidate",
            "since": "1.2.0-candidate",
            "implementation": "contracts/v1.2/system-shell-materials.candidate.json",
            "webPreview": "reference/v1.2/system-shell.html",
        }
    )
    projected.setdefault("capabilities", {})["frosted-neutral-system-shell"] = shell
    return projected


def validate_projection(projected: dict) -> None:
    req(projected.get("currentStable") == "1.1.0", "historical projection currentStable drifted")
    req(projected.get("currentOfficial") == "1.1.0", "historical projection currentOfficial drifted")
    req(projected.get("activeCandidate") == "1.2.0-candidate", "historical projection activeCandidate drifted")
    candidate = next(
        (item for item in projected.get("releases", []) if isinstance(item, dict) and item.get("version") == "1.2.0-candidate"),
        None,
    )
    req(candidate is not None, "historical Candidate release projection is missing")
    assert candidate is not None
    req(candidate.get("status") == "candidate", "historical projected release must remain Candidate")
    req(candidate.get("consumerEligible") is False, "historical Candidate projection cannot be consumer-eligible")
    req(candidate.get("stableBaseline") == "1.1.0", "historical Candidate baseline drifted")


def import_legacy(path: Path):
    req(path.is_file(), f"legacy validator missing: {path.relative_to(ROOT)}")
    spec = importlib.util.spec_from_file_location(path.stem, path)
    req(spec is not None and spec.loader is not None, f"cannot load {path.relative_to(ROOT)}")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_legacy_promoted_source(legacy_filename: str) -> int:
    live = validate_live_stable()
    projected = historical_projection(live)
    validate_projection(projected)
    legacy_path = ROOT / "scripts" / legacy_filename
    module = import_legacy(legacy_path)

    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", prefix=".glaze-v1.2-historical-version-", dir=ROOT
    ) as version_file, tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", suffix=".json", prefix=".glaze-v1.2-historical-lifecycle-", dir=ROOT
    ) as lifecycle_file:
        version_file.write("1.1.0\n")
        version_file.flush()
        json.dump(projected, lifecycle_file, indent=2)
        lifecycle_file.flush()
        version_path = Path(version_file.name)
        lifecycle_path = Path(lifecycle_file.name)

        for name in ("VERSION", "VERSION_PATH"):
            if hasattr(module, name):
                setattr(module, name, version_path)
        for name in ("LIFECYCLE", "LIFECYCLE_PATH"):
            if hasattr(module, name):
                setattr(module, name, lifecycle_path)

        # Inventory/naming validators package lifecycle checks in a helper that
        # reads ROOT directly. The projection is already validated above, so
        # replace only that global-boundary helper; all source/content checks stay intact.
        if hasattr(module, "validate_lifecycle"):
            module.validate_lifecycle = lambda: validate_projection(projected)

        # Living Glaze resolves VERSION through text() and lifecycle through
        # load(), rather than through path globals. Intercept only those two
        # historical authority reads and delegate all source reads unchanged.
        if legacy_filename == "validate_glaze_v1_2_living_glaze_legacy.py":
            original_text = module.text
            original_load = module.load

            def compatibility_text(path: str) -> str:
                if path == "VERSION":
                    return "1.1.0\n"
                return original_text(path)

            def compatibility_load(path: str):
                if path == "registry/lifecycle.json":
                    return copy.deepcopy(projected)
                return original_load(path)

            module.text = compatibility_text
            module.load = compatibility_load

        result = module.main()

    print(f"Promoted-source compatibility: PASS ({legacy_filename})")
    print("Authority: live V1.2 is Stable; historical lifecycle data was ephemeral validator-fixture state only.")
    return 0 if result is None else int(result)

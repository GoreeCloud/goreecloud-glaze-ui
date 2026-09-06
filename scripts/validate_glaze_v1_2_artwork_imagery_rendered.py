#!/usr/bin/env python3
"""Rendered acceptance for bounded GLAZE UI V1.2 Artwork, Illustration, and Imagery."""
from __future__ import annotations

import base64
import hashlib
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
WEB_PORT = 8805
DRIVER_PORT = 9555
SERVER = f"http://{HOST}:{WEB_PORT}"
DRIVER = f"http://{HOST}:{DRIVER_PORT}"
REFERENCE = "reference/v1.2/artwork-imagery.html"
CONTRACT = ROOT / "contracts/v1.2/artwork-imagery.candidate.json"
CSS = ROOT / "css/glaze-v1.2-artwork-imagery.candidate.css"
ENTRYPOINT = ROOT / "css/glaze-v1.2.0-candidate.css"
WORKFLOW = ROOT / ".github/workflows/glaze-v1.2-artwork-imagery.yml"
IDENTITY_ASSET = ROOT / "assets/identity/official/facet/glaze-ui-mark.svg"


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


def git_blob_sha1(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def validate_source() -> None:
    for path in (CONTRACT, CSS, ENTRYPOINT, WORKFLOW, IDENTITY_ASSET, ROOT / REFERENCE):
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")

    contract = load(CONTRACT)
    require(contract.get("version") == "1.2.0-candidate", "artwork Candidate version drifted")
    require(contract.get("lifecycle") == "candidate" and contract.get("consumerEligible") is False, "Artwork Candidate boundary drifted")
    require(contract.get("stableBaseline") == "1.1.0", "Stable baseline drifted")
    authority = contract.get("authority", {})
    require(authority.get("candidateMayCreateCanonicalProductArtwork") is False, "Candidate claimed canonical product-art authority")
    require(authority.get("candidateMayOverrideProductIdentity") is False, "Candidate claimed product-identity authority")

    expected_categories = {
        "identity-artwork", "functional-illustration", "atmospheric-artwork",
        "content-imagery", "technical-visualization", "editorial-imagery",
    }
    require(set(contract.get("categories", [])) == expected_categories, "artwork category model drifted")

    treatment = contract.get("treatmentRules", {})
    require(treatment.get("functionalPriority") == ["task", "content", "state", "interaction", "information-hierarchy", "artwork"], "artwork functional priority drifted")
    character = treatment.get("artworkCharacter", {})
    require(set(character.get("required", [])) == {"refined", "calm", "precise", "atmospheric", "recognizably-goreecloud", "contemporary", "purposeful"}, "V1.2 artwork character drifted")
    require(set(character.get("materialIdentity", [])) == {"light", "frost", "refraction", "geometry", "layering", "depth", "edge-illumination", "negative-space"}, "V1.2 artwork material identity drifted")
    require(character.get("literalGlassEverywhere") is False and character.get("routineHighSaturationGradientBranding") is False, "artwork restraint weakened")
    illustration = treatment.get("illustrationStyle", {})
    require(set(illustration.get("preferred", [])) == {"strong-silhouettes", "clean-geometric-construction", "controlled-depth", "soft-atmospheric-lighting", "restrained-detail", "deliberate-negative-space"}, "illustration style drifted")
    require(illustration.get("flatPresentationAllowedWhenItImprovesRecognitionAccessibilityOrCost") is True and illustration.get("restrainedDimensionalPresentationAllowed") is True, "illustration modality options drifted")
    require(illustration.get("chaoticVisualComplexity") is False and illustration.get("exaggeratedPlastic3d") is False, "illustration restraint weakened")
    hero = treatment.get("heroImagery", {})
    require(hero.get("routineProductivityDefault") is False, "hero artwork became a routine productivity default")
    require(set(hero.get("allowedContexts", [])) == {"major-first-use", "product-introduction", "immersive-content", "high-value-identity-moment"}, "hero artwork contexts drifted")
    require(hero.get("quietZonesRequiredFor") == ["title", "supporting-copy", "primary-action"] and hero.get("essentialTextMayOverlayBusiestRegion") is False, "hero quiet-zone/text protection drifted")
    empty = treatment.get("emptyState", {})
    require(empty.get("compact") is True and empty.get("optionalWhenUnnecessary") is True and empty.get("domainRelevantSymbolismRequired") is True, "empty-state artwork behavior drifted")
    require(empty.get("understandingPriority") == ["what-is-empty", "why-it-is-empty", "available-action"], "empty-state information priority drifted")
    require(empty.get("routineArtworkMayConsumeMostOfViewport") is False and empty.get("mayImplySuccessOrRecoveryBeforeAuthoritativeConfirmation") is False, "empty-state restraint/truth boundary weakened")
    wallpaper = treatment.get("wallpaper", {})
    require(wallpaper.get("role") == "background-non-semantic" and wallpaper.get("subordinateToApplicationContent") is True, "wallpaper hierarchy drifted")
    require(set(wallpaper.get("materialProtection", [])) == {"opacity", "saturation-reduction", "blur-or-equivalent-fallback", "local-contrast", "frost-density"}, "wallpaper material protection drifted")
    require(wallpaper.get("mayDetermineSemanticStatusFocusSecurityPrivacyOrCriticalMeaning") is False and wallpaper.get("requiredForGlazeIdentity") is False, "wallpaper gained semantic/identity authority")
    require(wallpaper.get("reducedMotionRequiresStillOrSimplifiedNonessentialMotion") is True and wallpaper.get("lowPerformanceMayUseStaticOrSimplifiedPresentation") is True, "wallpaper adaptation guards drifted")
    thumbnail = treatment.get("mediaThumbnail", {})
    require(thumbnail.get("contentRecognitionMustBePreserved") is True and thumbnail.get("minimalOverlaysOnly") is True, "thumbnail recognition/overlay policy drifted")
    require(set(thumbnail.get("allowedOverlays", [])) == {"duration", "media-type", "selection", "play-affordance"}, "thumbnail overlay model drifted")
    require(thumbnail.get("meaningfulSubjectCropPreferred") is True and thumbnail.get("loadingPlaceholderPreservesFinalAspectRatio") is True, "thumbnail crop/loading behavior drifted")
    screenshots = treatment.get("screenshots", {})
    require(screenshots.get("mustBeActualOrClearlyConceptual") is True and screenshots.get("mustRemainVersionAligned") is True, "screenshot truth/version policy drifted")
    require(set(screenshots.get("allowedFraming", [])) == {"subtle-device-frame", "frosted-surrounding-card", "clean-crop", "restrained-shadow"}, "screenshot framing drifted")
    require(screenshots.get("interfaceMustRemainReadable") is True and screenshots.get("speculativeMockupMayClaimImplementedBehavior") is False, "screenshot readability/truth boundary weakened")
    image = treatment.get("imageIntegration", {})
    require(image.get("cornerRadiusToken") == "--glz12-radius-surface" and image.get("cornerGeometryMustFollowSharedGlazeGeometry") is True, "image corner geometry drifted")
    overlay = image.get("frostOverlay", {})
    require(overlay.get("defaultRequired") is False and overlay.get("allowedWhen") == "text-overlaps-variable-imagery", "imagery frost-overlay policy drifted")
    require(overlay.get("mustPreserveContentRecognition") is True and overlay.get("reducedTransparencyFallbackRequired") is True, "imagery frost-overlay safeguards drifted")
    text_protection = image.get("textProtection", {})
    require(text_protection.get("liveInterfaceTypographyPreferred") is True and text_protection.get("essentialTextMustNotDependOnBusyImageRegion") is True, "image text-protection hierarchy drifted")
    require(text_protection.get("localContrastProtectionRequiredWhenTextOverlapsImagery") is True and text_protection.get("embeddedEssentialUntranslatedTextWithoutAlternativeAllowed") is False, "image text-protection accessibility drifted")
    tint = image.get("environmentalTint", {})
    require(tint.get("rawWallpaperOrImageSamplingOwnedByGlaze") is False and tint.get("producerSuppliedLocalRgbSummaryOnly") is True, "environmental tint authority drifted")
    require(tint.get("remoteSampling") is False and tint.get("semanticStateDerivation") is False and tint.get("reducedTransparencyMaySuppressDecorativeTint") is True, "environmental tint privacy/semantic guards drifted")

    provenance = contract.get("sourceAndProvenance", {})
    for key in (
        "sharedArtworkRequiresCanonicalSource",
        "consumersReferenceApprovedAssetsInsteadOfDriftingCopies",
        "materialIdentityChangesVersionedAndTraceable",
        "firstPartyIdentityArtworkRequiresExplicitOwnershipAndLifecycle",
        "thirdPartyLogosMustPreserveBrandIntegrity",
        "generatedMediaMustBeExplicitlyLabeledWhenConceptual",
        "screenshotsMustBeActualOrClearlyConceptualAndVersionAligned",
    ):
        require(provenance.get(key) is True, f"source/provenance guard drifted: {key}")
    require(provenance.get("remoteStockArtRequiredForGlazeIdentity") is False, "remote stock art became required")
    require(provenance.get("conceptualMediaMayClaimImplementedReality") is False, "conceptual media may claim implementation")

    identity = provenance.get("glazeUiIdentity", {})
    require(identity.get("authoritativeRepository") == "GoreeCloud/goreecloud-branding-assets", "Glaze identity authority repository drifted")
    require(identity.get("canonicalPath") == "systems/glaze-ui/glaze-ui-mark.svg", "Glaze identity canonical path drifted")
    require(identity.get("canonicalGitBlob") == "af8b70387bdaedb8d8388a1660b2d2ca29548fe2", "Glaze identity canonical blob drifted")
    require(identity.get("canonicalStatus") == "approved", "Glaze identity canonical approval status drifted")
    require(identity.get("consumerRepository") == "GoreeCloud/goreecloud-glaze-ui", "Glaze identity consumer repository drifted")
    require(identity.get("packagedDerivativePath") == "assets/identity/official/facet/glaze-ui-mark.svg", "Glaze identity packaged derivative path drifted")
    require(identity.get("packagedDerivativeMustMatchCanonicalBlob") is True, "Glaze identity derivative may drift from canonical source")
    require(identity.get("scope") == "glaze-ui-product-identity-only", "Glaze identity provenance scope broadened")
    require(identity.get("establishesSharedArtworkLibrary") is False, "Glaze identity provenance overclaimed a shared artwork library")
    local_identity_blob = git_blob_sha1(IDENTITY_ASSET.read_bytes())
    require(local_identity_blob == identity.get("canonicalGitBlob"), f"packaged Glaze identity drifted from approved canonical blob: {local_identity_blob}")

    truth = contract.get("truthBoundaries", {})
    for key in (
        "decorativeColorMayEncodeSemanticState",
        "illustrationMayManufactureHealthConnectivitySecurityPrivacyBackupOrRecoveryState",
        "emptyErrorRecoveryArtworkMayImplySuccessBeforeAuthoritativeConfirmation",
        "wallpaperMayDetermineSemanticStatusFocusSecurityPrivacyOrCriticalMeaning",
    ):
        require(truth.get(key) is False, f"truth boundary drifted: {key}")
    require(truth.get("technicalVisualizationMustPreserveAuthoritativeBoundaries") is True, "technical diagrams lost authority-boundary requirement")

    accessibility = contract.get("accessibility", {})
    require(accessibility.get("artworkMayBeSoleCarrierOfCriticalMeaning") is False, "artwork became sole critical-state carrier")
    for key in (
        "decorativeArtworkMustAvoidAssistiveTechnologyNoise",
        "informativeImageryRequiresEquivalentDescriptionOrSummary",
        "complexVisualizationRequiresTextualOrDataEquivalent",
        "forcedColorsMustRemainUnderstandable",
        "reducedTransparencyMustSuppressDecorativeFrostOverlays",
        "largeTextMustNotCauseHorizontalPageOverflow",
    ):
        require(accessibility.get(key) is True, f"accessibility media guard drifted: {key}")

    library = contract.get("referenceLibrary", {})
    require(library.get("containsCanonicalProductArtwork") is False, "reference contains canonical product artwork")
    require(library.get("containsThirdPartyLogoArtwork") is False, "reference contains third-party logo artwork")
    require(library.get("containsRemoteImages") is False, "reference contains remote images")
    require(library.get("containsDocumentaryPhotography") is False, "reference overclaims documentary imagery")
    require(library.get("containsConceptualCssGeometryOnly") is True, "reference is not bounded to CSS conceptual geometry")
    require(library.get("conceptualLabelRequired") == "Conceptual demonstration — not product-state evidence", "conceptual label drifted")

    prohibited = contract.get("prohibited", {})
    for key in (
        "copiedCanonicalProductArtwork", "unlabeledGeneratedDocumentaryMedia",
        "semanticStateByDecorationOnly", "decorativeRemoteAssetDependency",
        "thirdPartyLogoRecolorForAestheticFit", "blurredTechnicalLabels",
        "fabricatedHardwareCapability", "fabricatedSystemState",
    ):
        require(prohibited.get(key) is True, f"fail-closed artwork prohibition drifted: {key}")

    evidence = contract.get("evidenceBoundary", {})
    implemented = set(evidence.get("implemented", []))
    required_implemented = {
        "artwork-style-contract", "illustration-style-contract", "hero-imagery-treatment-contract",
        "empty-state-artwork-contract", "wallpaper-material-interaction-contract",
        "media-thumbnail-treatment-contract", "screenshot-treatment-contract",
        "image-corner-geometry-contract", "conditional-frost-overlay-contract",
        "image-text-protection-contract", "bounded-environmental-tint-contract",
        "functional-content-priority-contract", "approved-glaze-ui-identity-provenance",
    }
    require(required_implemented.issubset(implemented), "artwork treatment/provenance implementation evidence drifted")
    not_established = set(evidence.get("notEstablished", []))
    require({
        "canonical-v1.2-product-artwork-library", "shared-illustration-asset-library",
        "wallpaper-library", "photography-library", "human-artwork-review",
        "human-optical-acceptance", "native-platform-parity", "physical-device-acceptance",
        "release-candidate", "stable", "consumer-conformance",
    }.issubset(not_established), "artwork evidence boundary overclaims acceptance")

    css = CSS.read_text(encoding="utf-8")
    for marker in (
        ".glz12-concept-art", ".glz12-technical-diagram",
        'data-glz-transparency="reduced"', 'data-glz-text-scale="200"',
        "@media (forced-colors: active)", "background-image: none !important",
        "backdrop-filter: none",
    ):
        require(marker in css, f"artwork CSS marker missing: {marker}")
    for forbidden in ("url(", "data:image", "filter: blur(", "backdrop-filter: blur("):
        require(forbidden not in css, f"Artwork Candidate introduced external/blurred media dependency: {forbidden}")

    entry = ENTRYPOINT.read_text(encoding="utf-8")
    artwork_import = '@import url("./glaze-v1.2-artwork-imagery.candidate.css");'
    accessibility_import = '@import url("./glaze-v1.2-accessibility.candidate.css");'
    require(artwork_import in entry and accessibility_import in entry, "Candidate cascade missing artwork/accessibility layer")
    require(entry.index(artwork_import) < entry.index(accessibility_import), "artwork treatment must load before final accessibility authority")
    require(entry.strip().endswith(accessibility_import), "accessibility is no longer final in Candidate cascade")

    reference = (ROOT / REFERENCE).read_text(encoding="utf-8")
    for marker in (
        "Conceptual demonstration — not product-state evidence",
        "Recovery verification pending",
        "Decorative artwork cannot upgrade this state",
        "Producer-owned state",
        "Consumer presentation",
        "No drifting copies of shared artwork",
    ):
        require(marker in reference, f"artwork reference marker missing: {marker}")
    lowered = reference.lower()
    require("<img" not in lowered, "reference unexpectedly embeds image assets")
    require("http://" not in lowered and "https://" not in lowered, "reference unexpectedly depends on remote media")
    require('id="decorative-concept" class="glz12-concept-art" aria-hidden="true"' in reference, "decorative concept is not isolated from assistive technology")
    require('id="technical-diagram" class="glz12-technical-diagram" role="img" aria-describedby="technical-summary"' in reference, "technical visualization lacks equivalent description")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    require("validate_glaze_v1_2_artwork_imagery_rendered.py" in workflow, "workflow does not run artwork rendered validator")
    require("github.event.pull_request.head.sha || github.sha" in workflow, "artwork workflow is not exact-head pinned")
    require("assets/identity/official/facet/glaze-ui-mark.svg" in workflow, "artwork workflow does not watch the packaged canonical identity derivative")


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
    for item in (
        shutil.which("chromedriver"),
        "/usr/bin/chromedriver",
        "/usr/local/share/chromedriver-linux64/chromedriver",
    ):
        if item and Path(item).is_file():
            return str(item)
    raise AcceptanceError("chromedriver unavailable")


def execute(sid: str, script: str) -> Any:
    return request("POST", f"/session/{sid}/execute/sync", {"script": script, "args": []})


def cdp(sid: str, cmd: str, params: dict[str, Any] | None = None) -> Any:
    return request("POST", f"/session/{sid}/goog/cdp/execute", {"cmd": cmd, "params": params or {}})


def screenshot(sid: str, name: str) -> None:
    encoded = request("GET", f"/session/{sid}/screenshot")
    require(isinstance(encoded, str) and encoded, "no screenshot bytes")
    ARTIFACTS.mkdir(exist_ok=True)
    path = ARTIFACTS / f"glaze-v1.2-artwork-imagery-{name}.png"
    path.write_bytes(base64.b64decode(encoded))
    require(path.stat().st_size > 4000, f"invalid screenshot {path}")


def main() -> int:
    http = driver = None
    sid: str | None = None
    try:
        validate_source()
        ARTIFACTS.mkdir(exist_ok=True)
        http = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(WEB_PORT), "--bind", HOST, "--directory", str(ROOT)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        wait_http(f"{SERVER}/{REFERENCE}")
        driver = subprocess.Popen(
            [chromedriver(), f"--port={DRIVER_PORT}", "--allowed-ips=127.0.0.1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        wait_http(f"{DRIVER}/status")
        value = request(
            "POST",
            "/session",
            {"capabilities": {"alwaysMatch": {"browserName": "chrome", "goog:chromeOptions": {"args": [
                "--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
                "--disable-background-networking", "--disable-component-update",
                "--disable-extensions", "--disable-sync", "--metrics-recording-only",
                "--no-first-run", "--window-size=900,1000",
            ]}}}},
            timeout=60,
        )
        require(isinstance(value, dict) and isinstance(value.get("sessionId"), str), "Chrome returned no session id")
        sid = value["sessionId"]
        request("POST", f"/session/{sid}/url", {"url": f"{SERVER}/{REFERENCE}"})
        for _ in range(100):
            if execute(sid, "return document.readyState") == "complete":
                break
            time.sleep(.1)
        require(execute(sid, "return document.readyState") == "complete", "reference did not finish loading")

        resources = execute(sid, "return {images:document.images.length,srcs:Array.from(document.querySelectorAll('[src]')).map(x=>x.src),links:performance.getEntriesByType('resource').map(x=>x.name)}")
        require(resources.get("images") == 0, f"reference loaded embedded image assets: {resources}")
        remote = [u for u in resources.get("links", []) if isinstance(u, str) and not u.startswith(SERVER)]
        require(not remote, f"reference loaded remote assets: {remote}")

        initial = execute(sid, """const art=getComputedStyle(document.getElementById('decorative-concept'));const after=getComputedStyle(document.getElementById('decorative-concept'),'::after');const tech=getComputedStyle(document.getElementById('technical-diagram'));const warn=getComputedStyle(document.getElementById('warning-state'));return {bg:art.backgroundImage,after:after.display,filter:tech.filter,backdrop:tech.backdropFilter||tech.webkitBackdropFilter||'none',warningBorder:warn.borderInlineStartColor||warn.borderColor,label:document.getElementById('conceptual-label').textContent.trim()};""")
        require(initial.get("bg") not in (None, "", "none"), "conceptual CSS geometry did not render")
        require(initial.get("after") != "none", "conceptual geometry detail did not render")
        require(initial.get("filter") == "none" and initial.get("backdrop") in ("none", ""), f"technical labels received blur/filter treatment: {initial}")
        require(initial.get("label") == "Conceptual demonstration — not product-state evidence", "conceptual media label missing at runtime")
        screenshot(sid, "conceptual-treatment")

        execute(sid, "document.documentElement.dataset.glzAccent='rose';return true;")
        rose_warning = execute(sid, "const w=getComputedStyle(document.getElementById('warning-state'));return w.borderInlineStartColor||w.borderColor")
        require(rose_warning == initial.get("warningBorder"), "decorative accent changed protected warning-state treatment")

        execute(sid, "document.documentElement.dataset.glzTransparency='reduced';return true;")
        reduced = execute(sid, """const art=getComputedStyle(document.getElementById('decorative-concept'));const after=getComputedStyle(document.getElementById('decorative-concept'),'::after');return {bg:art.backgroundImage,after:after.display};""")
        require(reduced.get("bg") == "none" and reduced.get("after") == "none", f"Reduced Transparency did not suppress decorative media treatment: {reduced}")
        screenshot(sid, "reduced-transparency")

        execute(sid, "document.documentElement.removeAttribute('data-glz-transparency');return true;")
        cdp(sid, "Emulation.setEmulatedMedia", {"media": "screen", "features": [{"name": "forced-colors", "value": "active"}]})
        forced = execute(sid, """const art=getComputedStyle(document.getElementById('decorative-concept'));const after=getComputedStyle(document.getElementById('decorative-concept'),'::after');const tech=getComputedStyle(document.getElementById('technical-diagram'));return {bg:art.backgroundImage,after:after.display,techColor:tech.color};""")
        require(forced.get("bg") == "none" and forced.get("after") == "none", f"Forced Colors retained decorative imagery: {forced}")
        require(bool(forced.get("techColor")), "technical visualization lost readable color under Forced Colors")
        cdp(sid, "Emulation.setEmulatedMedia", {"media": "screen", "features": []})

        cdp(sid, "Emulation.setDeviceMetricsOverride", {"width": 320, "height": 1200, "deviceScaleFactor": 1, "mobile": False, "screenWidth": 320, "screenHeight": 1200})
        execute(sid, "document.documentElement.dataset.glzTextScale='200';document.documentElement.style.fontSize='200%';return true;")
        compact = execute(sid, """const d=getComputedStyle(document.getElementById('technical-diagram'));const label=document.getElementById('conceptual-label').getBoundingClientRect();return {scroll:document.documentElement.scrollWidth,inner:innerWidth,cols:d.gridTemplateColumns,labelRight:label.right,labelLeft:label.left};""")
        require(compact.get("scroll", 9999) <= compact.get("inner", 0) + 1, f"320px/200% text caused horizontal page overflow: {compact}")
        require(" " not in str(compact.get("cols", "")).strip(), f"technical visualization did not reflow to one column: {compact}")
        require(compact.get("labelLeft", -1) >= 0 and compact.get("labelRight", 9999) <= compact.get("inner", 0) + 1, f"conceptual label escaped compact viewport: {compact}")
        screenshot(sid, "compact-200")

        print("GLAZE UI V1.2 Artwork, Illustration, and Imagery rendered acceptance passed")
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
        for process in (driver, http):
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()


if __name__ == "__main__":
    raise SystemExit(main())

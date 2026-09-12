const CAPABILITY_ORDER = Object.freeze([
  'translucency',
  'backdrop-blur',
  'dynamic-opacity',
  'adaptive-frost',
  'aura',
  'edge-illumination',
  'material-aware-motion',
  'connected-transformation',
  'shadow-diffusion',
  'reduced-transparency',
  'increased-contrast',
  'reduced-motion'
]);

const NEVER_AUTO_DECLARE = Object.freeze([
  'environmental-sampling',
  'reflection',
  'hdr-aware-luminance'
]);

const MEDIA_QUERIES = Object.freeze({
  reducedTransparency: '(prefers-reduced-transparency: reduce)',
  reducedMotion: '(prefers-reduced-motion: reduce)',
  increasedContrast: '(prefers-contrast: more)',
  forcedColors: '(forced-colors: active)',
  darkAppearance: '(prefers-color-scheme: dark)'
});

function safeCssSupports(environment, property, value) {
  const css = environment?.CSS;
  if (!css || typeof css.supports !== 'function') return false;
  try {
    return css.supports.call(css, property, value) === true;
  } catch {
    return false;
  }
}

function safeMediaMatch(environment, query) {
  if (typeof environment?.matchMedia !== 'function') {
    return Object.freeze({available: false, matches: false});
  }
  try {
    const result = environment.matchMedia.call(environment, query);
    return Object.freeze({available: true, matches: result?.matches === true});
  } catch {
    return Object.freeze({available: false, matches: false});
  }
}

function hasWebAnimations(environment) {
  return typeof environment?.Element?.prototype?.animate === 'function';
}

function pushCapability(capabilities, capability, accepted) {
  if (accepted) capabilities.add(capability);
}

function freezeRecord(record) {
  return Object.freeze({...record});
}

/**
 * Detect only local, synchronous browser rendering capabilities that have bounded
 * feature tests. The adapter intentionally avoids browser identity, hardware
 * inventory, screen capture, network probes, persistence, telemetry, and analytics.
 */
export function detectBrowserOpticalCapabilities(environment = globalThis) {
  const translucency =
    safeCssSupports(environment, 'background-color', 'rgba(255, 255, 255, 0.5)') ||
    safeCssSupports(environment, 'background-color', 'rgb(255 255 255 / 0.5)');
  const backdropBlur =
    safeCssSupports(environment, 'backdrop-filter', 'blur(1px)') ||
    safeCssSupports(environment, '-webkit-backdrop-filter', 'blur(1px)');
  const dynamicOpacity =
    safeCssSupports(environment, 'opacity', '0.5') &&
    safeCssSupports(environment, 'transition-property', 'opacity');
  const aura =
    safeCssSupports(environment, 'background-image', 'radial-gradient(circle, transparent, black)') &&
    safeCssSupports(environment, 'filter', 'blur(1px)');
  const edgeIllumination =
    safeCssSupports(environment, 'background-image', 'linear-gradient(white, black)') &&
    safeCssSupports(environment, 'box-shadow', '0 0 0 1px currentColor');
  const shadowDiffusion = safeCssSupports(environment, 'box-shadow', '0 1px 3px rgba(0, 0, 0, 0.2)');
  const webAnimations = hasWebAnimations(environment);

  const mediaEvidence = freezeRecord({
    reducedTransparency: safeMediaMatch(environment, MEDIA_QUERIES.reducedTransparency),
    reducedMotion: safeMediaMatch(environment, MEDIA_QUERIES.reducedMotion),
    increasedContrast: safeMediaMatch(environment, MEDIA_QUERIES.increasedContrast),
    forcedColors: safeMediaMatch(environment, MEDIA_QUERIES.forcedColors),
    darkAppearance: safeMediaMatch(environment, MEDIA_QUERIES.darkAppearance)
  });

  const reducedTransparency = mediaEvidence.reducedTransparency.matches;
  const reducedMotion = mediaEvidence.reducedMotion.matches;
  const increasedContrast = mediaEvidence.increasedContrast.matches || mediaEvidence.forcedColors.matches;

  const capabilities = new Set();
  pushCapability(capabilities, 'translucency', translucency);
  pushCapability(capabilities, 'backdrop-blur', backdropBlur);
  pushCapability(capabilities, 'dynamic-opacity', dynamicOpacity);
  pushCapability(capabilities, 'adaptive-frost', translucency && backdropBlur && dynamicOpacity);
  pushCapability(capabilities, 'aura', aura);
  pushCapability(capabilities, 'edge-illumination', edgeIllumination);
  pushCapability(capabilities, 'material-aware-motion', webAnimations);
  pushCapability(capabilities, 'connected-transformation', webAnimations);
  pushCapability(capabilities, 'shadow-diffusion', shadowDiffusion);
  pushCapability(capabilities, 'reduced-transparency', reducedTransparency);
  pushCapability(capabilities, 'increased-contrast', increasedContrast);
  pushCapability(capabilities, 'reduced-motion', reducedMotion);

  const activePreferences = [];
  if (reducedTransparency) activePreferences.push('reduced-transparency');
  if (increasedContrast) activePreferences.push('increased-contrast');
  if (reducedMotion) activePreferences.push('reduced-motion');

  const recommendedAccessibilityProfile =
    reducedTransparency ? 'reduced-transparency' :
      increasedContrast ? 'increased-contrast' :
        reducedMotion ? 'reduced-motion' : 'standard';

  const orderedCapabilities = CAPABILITY_ORDER.filter(capability => capabilities.has(capability));

  return Object.freeze({
    kind: 'glaze-v1.4-browser-capability-snapshot-candidate',
    provenance: 'local-synchronous-feature-detection',
    capabilities: Object.freeze(orderedCapabilities),
    neverAutoDeclared: NEVER_AUTO_DECLARE,
    activeAccessibilityPreferences: Object.freeze(activePreferences),
    recommendedAccessibilityProfile,
    recommendedAppearanceMode: mediaEvidence.darkAppearance.matches ? 'dark' : 'light',
    multipleAccessibilityPreferencesActive: activePreferences.length > 1,
    recommendationIsQualificationEvidence: false,
    evidence: Object.freeze({
      cssSupportsAvailable: typeof environment?.CSS?.supports === 'function',
      matchMediaAvailable: typeof environment?.matchMedia === 'function',
      translucency,
      backdropBlur,
      dynamicOpacity,
      aura,
      edgeIllumination,
      shadowDiffusion,
      webAnimations,
      media: mediaEvidence
    }),
    privacy: Object.freeze({
      identitySniffingUsed: false,
      hardwareInventoryUsed: false,
      batteryStateUsed: false,
      networkProbeUsed: false,
      screenCaptureUsed: false,
      persistentStorageUsed: false,
      telemetryUsed: false,
      analyticsUsed: false,
      remoteAssetsRequired: false
    }),
    qualification: Object.freeze({
      browserMatrixEstablished: false,
      assistiveTechnologyEstablished: false,
      physicalDeviceEstablished: false,
      productionPerformanceEstablished: false
    })
  });
}

export function createBrowserOpticalCapabilityAdapter({environment = globalThis} = {}) {
  return Object.freeze({
    kind: 'glaze-v1.4-browser-capability-adapter-candidate',
    telemetryRequired: false,
    analyticsRequired: false,
    persistentStorageRequired: false,
    networkAccessRequired: false,
    screenCaptureRequired: false,
    browserQualificationEstablished: false,
    resolve() {
      return detectBrowserOpticalCapabilities(environment).capabilities;
    },
    snapshot() {
      return detectBrowserOpticalCapabilities(environment);
    },
    prepareRequest(request = {}) {
      const snapshot = detectBrowserOpticalCapabilities(environment);
      const prepared = {
        ...request,
        platformCapabilities: request.platformCapabilities ?? snapshot.capabilities,
        accessibilityProfile: request.accessibilityProfile ?? snapshot.recommendedAccessibilityProfile,
        appearanceMode: request.appearanceMode ?? snapshot.recommendedAppearanceMode
      };
      return Object.freeze({
        request: Object.freeze(prepared),
        snapshot,
        consumerPolicyRequired: snapshot.multipleAccessibilityPreferencesActive
      });
    }
  });
}

export const browserCapabilityCandidate = Object.freeze({
  targetVersion: '1.4.0-candidate',
  releaseLifecycle: 'proposed',
  consumerEligible: false,
  lifecycleAuthority: false,
  semanticApiStability: 'candidate-not-frozen',
  stableSource: '1.3.0',
  telemetryRequired: false,
  analyticsRequired: false,
  persistentStorageRequired: false,
  networkAccessRequired: false,
  screenCaptureRequired: false,
  environmentalSamplingAutoDeclared: false,
  reflectionAutoDeclared: false,
  hdrAwareLuminanceAutoDeclared: false,
  browserMatrixQualificationEstablished: false,
  assistiveTechnologyQualificationEstablished: false,
  physicalDeviceQualificationEstablished: false,
  productionPerformanceQualificationEstablished: false,
  nativeRendererParityEstablished: false
});

const MATERIAL_ROLES = Object.freeze({
  'glz.material.canvas': Object.freeze({opticalProfile: 'subdued'}),
  'glz.material.surface': Object.freeze({opticalProfile: 'standard'}),
  'glz.material.softGlaze': Object.freeze({opticalProfile: 'subdued'}),
  'glz.material.glaze': Object.freeze({opticalProfile: 'standard'}),
  'glz.material.deepGlaze': Object.freeze({opticalProfile: 'deep'}),
  'glz.material.liveGlaze': Object.freeze({
    opticalProfile: 'elevated',
    optionalCapabilities: Object.freeze([
      'environmental-sampling',
      'dynamic-opacity',
      'adaptive-frost'
    ])
  })
});

const ELEVATION_ROLES = Object.freeze({
  'glz.elevation.embedded': 'subdued',
  'glz.elevation.raised': 'standard',
  'glz.elevation.interactive': 'standard',
  'glz.elevation.floating': 'elevated',
  'glz.elevation.modal': 'deep',
  'glz.elevation.focus': 'transient'
});

const INTERACTION_STATES = new Set([
  'rest', 'hover', 'focus', 'pressed', 'dragged', 'selected', 'expanded', 'loading', 'disabled'
]);
const APPEARANCE_MODES = new Set(['light', 'dark', 'deep-dark']);
const ACCESSIBILITY_PROFILES = new Set([
  'standard',
  'reduced-transparency',
  'increased-contrast',
  'reduced-motion',
  'large-text',
  'color-vision-accommodation',
  'low-power-performance-constrained'
]);
const PERFORMANCE_LEVELS = new Set(['full', 'balanced', 'efficient']);
const ENVIRONMENTAL_MODES = new Set(['disabled', 'static', 'adaptive']);
const KNOWN_CAPABILITIES = Object.freeze([
  'backdrop-blur',
  'translucency',
  'dynamic-opacity',
  'environmental-sampling',
  'reflection',
  'adaptive-frost',
  'aura',
  'edge-illumination',
  'material-aware-motion',
  'connected-transformation',
  'shadow-diffusion',
  'hdr-aware-luminance',
  'reduced-transparency',
  'increased-contrast',
  'reduced-motion'
]);
const PROFILE_STRENGTH = Object.freeze({subdued: 0, standard: 1, transient: 2, elevated: 3, deep: 4});
const DISPOSITION_STRENGTH = Object.freeze({accepted: 0, downgraded: 1, substituted: 2, rejected: 3});

function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function oneOf(value, allowed, fallback) {
  return allowed.has(value) ? value : fallback;
}

function strongerProfile(left, right) {
  return PROFILE_STRENGTH[right] > PROFILE_STRENGTH[left] ? right : left;
}

function strongerDisposition(current, next) {
  return DISPOSITION_STRENGTH[next] > DISPOSITION_STRENGTH[current] ? next : current;
}

function normalizeCapabilities(value) {
  const declared = new Set();
  const unknown = new Set();
  const add = (capability, enabled = true) => {
    if (!enabled || typeof capability !== 'string') return;
    if (KNOWN_CAPABILITIES.includes(capability)) declared.add(capability);
    else unknown.add(capability);
  };

  if (value instanceof Set || Array.isArray(value)) {
    for (const capability of value) add(capability, true);
  } else if (isObject(value)) {
    for (const [capability, enabled] of Object.entries(value)) add(capability, enabled === true);
  }

  const evidence = {};
  for (const capability of KNOWN_CAPABILITIES) evidence[capability] = declared.has(capability);
  return Object.freeze({
    declared: Object.freeze([...declared].sort()),
    unknown: Object.freeze([...unknown].sort()),
    evidence: Object.freeze(evidence),
    source: 'explicit-runtime-declaration'
  });
}

function normalizeEnvironmentalResponse(value) {
  const input = isObject(value) ? value : {mode: value};
  return Object.freeze({
    mode: oneOf(input.mode, ENVIRONMENTAL_MODES, 'static'),
    protectedSurface: Boolean(input.protectedSurface),
    privacyRestrictedSurface: Boolean(input.privacyRestrictedSurface)
  });
}

function freezeRequest(value) {
  const input = isObject(value) ? value : {};
  return Object.freeze({
    materialRole: typeof input.materialRole === 'string' ? input.materialRole : 'glz.material.surface',
    elevationRole: typeof input.elevationRole === 'string' ? input.elevationRole : 'glz.elevation.raised',
    interactionState: typeof input.interactionState === 'string' ? input.interactionState : 'rest',
    appearanceMode: typeof input.appearanceMode === 'string' ? input.appearanceMode : 'light',
    accessibilityProfile: typeof input.accessibilityProfile === 'string' ? input.accessibilityProfile : 'standard',
    performanceLevel: typeof input.performanceLevel === 'string' ? input.performanceLevel : 'balanced',
    environmentalResponse: normalizeEnvironmentalResponse(input.environmentalResponse),
    platformCapabilities: input.platformCapabilities ?? []
  });
}

function normalizeSemanticRequest(request, reasons) {
  let disposition = 'accepted';
  let materialRole = request.materialRole;
  let elevationRole = request.elevationRole;
  let interactionState = request.interactionState;
  let appearanceMode = request.appearanceMode;
  let accessibilityProfile = request.accessibilityProfile;
  let performanceLevel = request.performanceLevel;

  if (!Object.hasOwn(MATERIAL_ROLES, materialRole)) {
    materialRole = 'glz.material.surface';
    reasons.push('unknown-material-role-substituted');
    disposition = strongerDisposition(disposition, 'substituted');
  }
  if (!Object.hasOwn(ELEVATION_ROLES, elevationRole)) {
    elevationRole = 'glz.elevation.raised';
    reasons.push('unknown-elevation-role-substituted');
    disposition = strongerDisposition(disposition, 'substituted');
  }
  if (!INTERACTION_STATES.has(interactionState)) {
    interactionState = 'rest';
    reasons.push('unknown-interaction-state-substituted');
    disposition = strongerDisposition(disposition, 'substituted');
  }
  if (!APPEARANCE_MODES.has(appearanceMode)) {
    appearanceMode = 'light';
    reasons.push('unknown-appearance-mode-substituted');
    disposition = strongerDisposition(disposition, 'substituted');
  }
  if (!ACCESSIBILITY_PROFILES.has(accessibilityProfile)) {
    accessibilityProfile = 'standard';
    reasons.push('unknown-accessibility-profile-substituted');
    disposition = strongerDisposition(disposition, 'substituted');
  }
  if (!PERFORMANCE_LEVELS.has(performanceLevel)) {
    performanceLevel = 'balanced';
    reasons.push('unknown-performance-level-substituted');
    disposition = strongerDisposition(disposition, 'substituted');
  }

  return {
    materialRole,
    elevationRole,
    interactionState,
    appearanceMode,
    accessibilityProfile,
    performanceLevel,
    disposition
  };
}

function effectMap(capabilities, options) {
  const has = capability => capabilities.evidence[capability] === true;
  const efficient = options.performanceLevel === 'efficient';
  const full = options.performanceLevel === 'full';
  const reducedMotion = options.accessibilityProfile === 'reduced-motion';
  const increasedContrast = options.accessibilityProfile === 'increased-contrast';
  const solid = options.renderingMode === 'solid-semantic-surface';
  const adaptive = options.environmentalMode === 'adaptive';

  return Object.freeze({
    translucency: !solid && has('translucency'),
    backdropBlur: !solid && !efficient && has('backdrop-blur'),
    dynamicOpacity: adaptive && has('dynamic-opacity'),
    environmentalSampling: adaptive && has('environmental-sampling'),
    reflection: !solid && full && !increasedContrast && has('reflection'),
    adaptiveFrost: adaptive && has('adaptive-frost'),
    aura: !solid && full && !increasedContrast && has('aura'),
    edgeIllumination: !solid && !efficient && !increasedContrast && has('edge-illumination'),
    materialAwareMotion: !solid && full && !reducedMotion && has('material-aware-motion'),
    connectedTransformation: !solid && full && !reducedMotion && has('connected-transformation'),
    shadowDiffusion: !solid && !efficient && has('shadow-diffusion'),
    hdrAwareLuminance: !solid && !efficient && has('hdr-aware-luminance')
  });
}

export function resolveOpticalRuntime(request = {}) {
  const requested = freezeRequest(request);
  const reasons = [];
  const fallbacks = [];
  const normalized = normalizeSemanticRequest(requested, reasons);
  let disposition = normalized.disposition;
  let performanceLevel = normalized.performanceLevel;
  const capabilities = normalizeCapabilities(requested.platformCapabilities);

  if (request.platformCapabilities == null) {
    reasons.push('platform-capabilities-not-declared');
  }
  if (capabilities.unknown.length > 0) {
    reasons.push('unknown-capabilities-treated-as-unsupported');
  }

  if (normalized.accessibilityProfile === 'low-power-performance-constrained' && performanceLevel !== 'efficient') {
    performanceLevel = 'efficient';
    reasons.push('accessibility-profile-forced-efficient-performance');
  }

  let effectiveOpticalProfile = strongerProfile(
    MATERIAL_ROLES[normalized.materialRole].opticalProfile,
    ELEVATION_ROLES[normalized.elevationRole]
  );
  if (normalized.interactionState === 'focus') {
    effectiveOpticalProfile = strongerProfile(effectiveOpticalProfile, 'transient');
  }

  let renderingMode = 'optical-glaze';
  if (normalized.accessibilityProfile === 'reduced-transparency') {
    renderingMode = 'solid-semantic-surface';
    effectiveOpticalProfile = 'solid-semantic-surface';
    fallbacks.push('solid-semantic-surface');
    reasons.push('reduced-transparency-forced-solid-material');
    disposition = strongerDisposition(disposition, 'substituted');
  } else if (!capabilities.evidence.translucency) {
    renderingMode = 'solid-semantic-surface';
    effectiveOpticalProfile = 'solid-semantic-surface';
    fallbacks.push('solid-semantic-surface');
    reasons.push('translucency-capability-unavailable');
    disposition = strongerDisposition(disposition, 'substituted');
  } else if (performanceLevel === 'efficient') {
    renderingMode = 'static-glaze';
    fallbacks.push('static-or-solid-material');
    reasons.push('efficient-performance-selected-static-material');
  } else if (!capabilities.evidence['backdrop-blur']) {
    renderingMode = 'static-glaze';
    fallbacks.push('static-or-solid-material');
    reasons.push('backdrop-blur-capability-unavailable');
    disposition = strongerDisposition(disposition, 'downgraded');
  }

  const environment = requested.environmentalResponse;
  let environmentalMode = environment.mode;
  if (environment.protectedSurface || environment.privacyRestrictedSurface) {
    if (environmentalMode === 'adaptive') {
      environmentalMode = 'static';
      fallbacks.push('governed-static-semantic-material');
      reasons.push(environment.protectedSurface
        ? 'protected-surface-disables-environmental-sampling'
        : 'privacy-restricted-surface-disables-environmental-sampling');
      disposition = strongerDisposition(disposition, 'downgraded');
    }
  }

  if (environmentalMode === 'adaptive' && normalized.materialRole !== 'glz.material.liveGlaze') {
    environmentalMode = 'static';
    fallbacks.push('governed-static-semantic-material');
    reasons.push('adaptive-environmental-response-requires-live-glaze');
    disposition = strongerDisposition(disposition, 'downgraded');
  }

  if (environmentalMode === 'adaptive' && performanceLevel !== 'full') {
    environmentalMode = 'static';
    fallbacks.push('governed-static-semantic-material');
    reasons.push('adaptive-environmental-response-requires-full-performance-level');
    disposition = strongerDisposition(disposition, 'downgraded');
  }

  if (environmentalMode === 'adaptive' && renderingMode === 'solid-semantic-surface') {
    environmentalMode = 'static';
    fallbacks.push('governed-static-semantic-material');
    reasons.push('solid-material-disables-environmental-sampling');
    disposition = strongerDisposition(disposition, 'downgraded');
  }

  if (environmentalMode === 'adaptive') {
    const required = MATERIAL_ROLES['glz.material.liveGlaze'].optionalCapabilities;
    const missing = required.filter(capability => capabilities.evidence[capability] !== true);
    if (missing.length > 0) {
      environmentalMode = 'static';
      fallbacks.push('governed-static-semantic-material');
      reasons.push(`adaptive-environmental-capabilities-unavailable:${missing.join(',')}`);
      disposition = strongerDisposition(disposition, 'downgraded');
    }
  }

  if (normalized.accessibilityProfile === 'reduced-motion') {
    fallbacks.push('inherited-v1.3-reduced-motion');
  }

  const effects = effectMap(capabilities, {
    performanceLevel,
    accessibilityProfile: normalized.accessibilityProfile,
    renderingMode,
    environmentalMode
  });

  const accepted = Object.freeze({
    materialRole: normalized.materialRole,
    elevationRole: normalized.elevationRole,
    interactionState: normalized.interactionState,
    appearanceMode: normalized.appearanceMode,
    accessibilityProfile: normalized.accessibilityProfile,
    performanceLevel,
    environmentalResponse: Object.freeze({
      mode: environmentalMode,
      localOnly: true,
      ephemeral: true,
      remoteTransmissionAllowed: false,
      persistentHistoryAllowed: false
    }),
    platformCapabilities: capabilities.declared,
    renderingMode,
    effects
  });

  return Object.freeze({
    requested,
    accepted,
    disposition,
    reasons: Object.freeze([...new Set(reasons)]),
    effectiveOpticalProfile,
    capabilityEvidence: capabilities,
    fallbacks: Object.freeze([...new Set(fallbacks)])
  });
}

function rootOf(target) {
  if (!target) throw new TypeError('An optical runtime target is required');
  return target.documentElement || target;
}

export function applyOpticalRuntime(target, request = {}) {
  const element = rootOf(target);
  if (!element.dataset || !element.style || typeof element.style.setProperty !== 'function') {
    throw new TypeError('Optical runtime target must expose dataset and style.setProperty');
  }
  const resolved = resolveOpticalRuntime(request);
  const effects = resolved.accepted.effects;
  element.dataset.glazeV14Material = resolved.accepted.materialRole;
  element.dataset.glazeV14Disposition = resolved.disposition;
  element.dataset.glazeV14Profile = resolved.effectiveOpticalProfile;
  element.dataset.glazeV14Rendering = resolved.accepted.renderingMode;
  element.dataset.glazeV14Environment = resolved.accepted.environmentalResponse.mode;
  element.style.setProperty('--glz14-optical-profile', resolved.effectiveOpticalProfile);
  element.style.setProperty('--glz14-translucency-enabled', effects.translucency ? '1' : '0');
  element.style.setProperty('--glz14-backdrop-blur-enabled', effects.backdropBlur ? '1' : '0');
  element.style.setProperty('--glz14-environmental-sampling-enabled', effects.environmentalSampling ? '1' : '0');
  element.style.setProperty('--glz14-reflection-enabled', effects.reflection ? '1' : '0');
  element.style.setProperty('--glz14-aura-enabled', effects.aura ? '1' : '0');
  element.style.setProperty('--glz14-material-motion-enabled', effects.materialAwareMotion ? '1' : '0');
  return resolved;
}

export function createOpticalRuntimeResolver({capabilityAdapter = null} = {}) {
  return Object.freeze({
    kind: 'glaze-v1.4-semantic-optical-runtime-candidate',
    telemetryRequired: false,
    analyticsRequired: false,
    resolve(request = {}) {
      const declared = request.platformCapabilities ?? (
        typeof capabilityAdapter?.resolve === 'function' ? capabilityAdapter.resolve() : []
      );
      return resolveOpticalRuntime({...request, platformCapabilities: declared});
    },
    apply(target, request = {}) {
      const declared = request.platformCapabilities ?? (
        typeof capabilityAdapter?.resolve === 'function' ? capabilityAdapter.resolve() : []
      );
      return applyOpticalRuntime(target, {...request, platformCapabilities: declared});
    }
  });
}

export const opticalRuntimeCandidate = Object.freeze({
  targetVersion: '1.4.0-candidate',
  releaseLifecycle: 'proposed',
  consumerEligible: false,
  lifecycleAuthority: false,
  semanticApiStability: 'candidate-not-frozen',
  stableSource: '1.3.0',
  telemetryRequired: false,
  analyticsRequired: false,
  remoteEnvironmentalSamplingAllowed: false,
  productionPerformanceBudgetsEstablished: false,
  physicalDeviceQualificationEstablished: false,
  nativeRendererParityEstablished: false,
  establishesOperationalSecurityAuthority: false,
  establishesOperationalPrivacyAuthority: false,
  establishesIdentityAuthority: false,
  establishesRecoveryAuthority: false
});

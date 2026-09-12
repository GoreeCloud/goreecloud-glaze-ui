import {
  opticalRuntimeCandidate,
  resolveOpticalRuntime
} from './glaze-v1.4-optical-runtime.candidate.mjs';

const REQUIREMENT_ORDER = Object.freeze([
  'reduced-transparency',
  'forced-colors',
  'increased-contrast',
  'reduced-motion',
  'low-power-performance-constrained',
  'large-text',
  'color-vision-accommodation'
]);
const SUPPORTED_REQUIREMENTS = new Set(REQUIREMENT_ORDER);
const LEGACY_PROFILES = new Set([
  'standard',
  'reduced-transparency',
  'increased-contrast',
  'reduced-motion',
  'large-text',
  'color-vision-accommodation',
  'low-power-performance-constrained'
]);
const DISPOSITION_STRENGTH = Object.freeze({accepted: 0, downgraded: 1, substituted: 2, rejected: 3});

function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function strongerDisposition(current, next) {
  return DISPOSITION_STRENGTH[next] > DISPOSITION_STRENGTH[current] ? next : current;
}

function requirementValues(value) {
  if (value instanceof Set || Array.isArray(value)) return [...value];
  return value == null ? [] : [value];
}

function normalizeAccessibilityRequest(request) {
  const input = isObject(request) ? request : {};
  const requirements = new Set();
  const unknown = new Set();
  const rawRequirements = requirementValues(input.accessibilityRequirements);

  for (const value of rawRequirements) {
    if (typeof value !== 'string') {
      unknown.add(String(value));
      continue;
    }
    if (SUPPORTED_REQUIREMENTS.has(value)) requirements.add(value);
    else unknown.add(value);
  }

  const legacyProfile = typeof input.accessibilityProfile === 'string'
    ? input.accessibilityProfile
    : 'standard';
  let unknownLegacyProfile = null;
  if (!LEGACY_PROFILES.has(legacyProfile)) {
    unknownLegacyProfile = legacyProfile;
  } else if (legacyProfile !== 'standard') {
    requirements.add(legacyProfile);
  }

  const orderedRequirements = REQUIREMENT_ORDER.filter(value => requirements.has(value));
  const summaryProfile = orderedRequirements.includes('reduced-transparency')
    ? 'reduced-transparency'
    : orderedRequirements.includes('forced-colors') || orderedRequirements.includes('increased-contrast')
      ? 'increased-contrast'
      : orderedRequirements.includes('reduced-motion')
        ? 'reduced-motion'
        : orderedRequirements.includes('low-power-performance-constrained')
          ? 'low-power-performance-constrained'
          : orderedRequirements.includes('large-text')
            ? 'large-text'
            : orderedRequirements.includes('color-vision-accommodation')
              ? 'color-vision-accommodation'
              : 'standard';

  return Object.freeze({
    requirements: Object.freeze(orderedRequirements),
    unknown: Object.freeze([...unknown].sort()),
    legacyProfile,
    unknownLegacyProfile,
    summaryProfile
  });
}

function composedEffects(baseEffects, requirements) {
  const active = new Set(requirements);
  const contrastFirst = active.has('increased-contrast') || active.has('forced-colors');
  const reducedMotion = active.has('reduced-motion');

  return Object.freeze({
    ...baseEffects,
    reflection: contrastFirst ? false : baseEffects.reflection,
    aura: contrastFirst ? false : baseEffects.aura,
    edgeIllumination: contrastFirst ? false : baseEffects.edgeIllumination,
    materialAwareMotion: reducedMotion ? false : baseEffects.materialAwareMotion,
    connectedTransformation: reducedMotion ? false : baseEffects.connectedTransformation
  });
}

/**
 * Compose simultaneous accessibility requirements above the scalar semantic
 * optical resolver. The legacy accessibilityProfile remains a compatibility
 * summary only; behavior is governed by the full accessibilityRequirements set.
 */
export function resolveAccessibleOpticalRuntime(request = {}) {
  const input = isObject(request) ? request : {};
  const composition = normalizeAccessibilityRequest(input);
  const reasons = [];
  const fallbacks = [];
  let disposition = 'accepted';

  if (composition.unknownLegacyProfile) {
    reasons.push(`unknown-accessibility-profile-substituted:${composition.unknownLegacyProfile}`);
    disposition = strongerDisposition(disposition, 'substituted');
  }
  if (composition.unknown.length > 0) {
    reasons.push(`unknown-accessibility-requirements-ignored:${composition.unknown.join(',')}`);
    disposition = strongerDisposition(disposition, 'substituted');
  }
  if (composition.requirements.length > 1) {
    reasons.push('composed-accessibility-requirements-preserved');
  }

  const constrainedPerformance = composition.requirements.includes('low-power-performance-constrained');
  const baseRequest = {
    ...input,
    accessibilityProfile: composition.summaryProfile,
    performanceLevel: constrainedPerformance ? 'efficient' : input.performanceLevel
  };
  delete baseRequest.accessibilityRequirements;

  const base = resolveOpticalRuntime(baseRequest);
  disposition = strongerDisposition(disposition, base.disposition);
  reasons.push(...base.reasons);
  fallbacks.push(...base.fallbacks);

  if (composition.requirements.includes('forced-colors')) {
    reasons.push('forced-colors-preserved-as-independent-requirement');
    fallbacks.push('system-color-compatible-material');
  }
  if (composition.requirements.includes('increased-contrast')) {
    reasons.push('increased-contrast-suppressed-optional-atmospheric-effects');
  }
  if (composition.requirements.includes('reduced-motion')) {
    reasons.push('reduced-motion-disabled-optional-material-motion');
    fallbacks.push('inherited-v1.3-reduced-motion');
  }
  if (constrainedPerformance) {
    reasons.push('composed-low-power-performance-forced-efficient-level');
    fallbacks.push('static-or-solid-material');
  }
  if (composition.requirements.includes('large-text')) {
    reasons.push('large-text-requirement-preserved-for-layout-policy');
  }
  if (composition.requirements.includes('color-vision-accommodation')) {
    reasons.push('color-vision-requirement-preserved-for-redundant-state-cues');
  }

  const acceptedEffects = composedEffects(base.accepted.effects, composition.requirements);
  const accepted = Object.freeze({
    ...base.accepted,
    accessibilityProfile: composition.summaryProfile,
    accessibilityRequirements: composition.requirements,
    effects: acceptedEffects
  });

  const requested = Object.freeze({
    ...base.requested,
    accessibilityProfile: composition.legacyProfile,
    accessibilityRequirements: Object.freeze(
      requirementValues(input.accessibilityRequirements)
        .filter(value => typeof value === 'string')
    )
  });

  return Object.freeze({
    ...base,
    requested,
    accepted,
    disposition,
    reasons: Object.freeze([...new Set(reasons)]),
    fallbacks: Object.freeze([...new Set(fallbacks)]),
    accessibilityComposition: Object.freeze({
      requirements: composition.requirements,
      legacySummaryProfile: composition.summaryProfile,
      legacySummaryIsBehaviorAuthority: false,
      requirementsAreBehaviorAuthority: true,
      unknownRequirements: composition.unknown,
      source: 'v1.4-accessibility-composition-candidate'
    })
  });
}

export function createAccessibleOpticalRuntimeResolver({capabilityAdapter = null} = {}) {
  return Object.freeze({
    kind: 'glaze-v1.4-accessibility-optical-runtime-candidate',
    telemetryRequired: false,
    analyticsRequired: false,
    resolve(request = {}) {
      const declared = request.platformCapabilities ?? (
        typeof capabilityAdapter?.resolve === 'function' ? capabilityAdapter.resolve() : []
      );
      return resolveAccessibleOpticalRuntime({...request, platformCapabilities: declared});
    }
  });
}

export const accessibilityCompositionCandidate = Object.freeze({
  targetVersion: opticalRuntimeCandidate.targetVersion,
  releaseLifecycle: 'proposed',
  consumerEligible: false,
  lifecycleAuthority: false,
  semanticApiStability: 'candidate-not-frozen',
  stableSource: '1.3.0',
  legacyAccessibilityProfileStillAccepted: true,
  simultaneousRequirementsPreserved: true,
  requirementsAreBehaviorAuthority: true,
  legacySummaryIsBehaviorAuthority: false,
  forcedColorsPreservedIndependently: true,
  telemetryRequired: false,
  analyticsRequired: false,
  browserMatrixQualificationEstablished: false,
  assistiveTechnologyQualificationEstablished: false,
  physicalDeviceQualificationEstablished: false,
  productionPerformanceQualificationEstablished: false,
  nativeRendererParityEstablished: false
});

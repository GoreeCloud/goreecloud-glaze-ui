import test from 'node:test';
import assert from 'node:assert/strict';

import {
  applyOpticalRuntime,
  createOpticalRuntimeResolver,
  opticalRuntimeCandidate,
  resolveOpticalRuntime
} from '../js/glaze-v1.4-optical-runtime.candidate.mjs';

const BASE_CAPABILITIES = [
  'translucency',
  'backdrop-blur',
  'shadow-diffusion'
];

const FULL_LIVE_CAPABILITIES = [
  ...BASE_CAPABILITIES,
  'dynamic-opacity',
  'environmental-sampling',
  'adaptive-frost',
  'reflection',
  'aura',
  'edge-illumination',
  'material-aware-motion',
  'connected-transformation',
  'hdr-aware-luminance'
];

test('unknown capabilities fail closed and no capability is accepted implicitly', () => {
  const result = resolveOpticalRuntime({
    materialRole: 'glz.material.glaze',
    platformCapabilities: ['future-optics']
  });
  assert.equal(result.disposition, 'substituted');
  assert.equal(result.accepted.renderingMode, 'solid-semantic-surface');
  assert.equal(result.capabilityEvidence.evidence.translucency, false);
  assert.deepEqual(result.capabilityEvidence.unknown, ['future-optics']);
  assert.ok(result.reasons.includes('unknown-capabilities-treated-as-unsupported'));
});

test('standard material is accepted when baseline optical capabilities are explicitly declared', () => {
  const result = resolveOpticalRuntime({
    materialRole: 'glz.material.glaze',
    elevationRole: 'glz.elevation.raised',
    platformCapabilities: BASE_CAPABILITIES
  });
  assert.equal(result.disposition, 'accepted');
  assert.equal(result.effectiveOpticalProfile, 'standard');
  assert.equal(result.accepted.renderingMode, 'optical-glaze');
  assert.equal(result.accepted.effects.translucency, true);
  assert.equal(result.accepted.effects.backdropBlur, true);
});

test('elevation and focus preserve semantic hierarchy without exposing raw optical values', () => {
  const result = resolveOpticalRuntime({
    materialRole: 'glz.material.canvas',
    elevationRole: 'glz.elevation.focus',
    interactionState: 'focus',
    platformCapabilities: BASE_CAPABILITIES
  });
  assert.equal(result.effectiveOpticalProfile, 'transient');
  assert.equal(Object.hasOwn(result, 'opticalDepth'), false);
  assert.equal(Object.hasOwn(result.accepted, 'opticalDepth'), false);
});

test('reduced transparency overrides declared optical capabilities with a designed solid material', () => {
  const result = resolveOpticalRuntime({
    materialRole: 'glz.material.deepGlaze',
    elevationRole: 'glz.elevation.modal',
    accessibilityProfile: 'reduced-transparency',
    performanceLevel: 'full',
    environmentalResponse: {mode: 'adaptive'},
    platformCapabilities: FULL_LIVE_CAPABILITIES
  });
  assert.equal(result.disposition, 'substituted');
  assert.equal(result.accepted.renderingMode, 'solid-semantic-surface');
  assert.equal(result.effectiveOpticalProfile, 'solid-semantic-surface');
  assert.equal(result.accepted.effects.translucency, false);
  assert.equal(result.accepted.effects.environmentalSampling, false);
  assert.ok(result.fallbacks.includes('solid-semantic-surface'));
});

test('live glaze adaptive response is accepted only with explicit full capability evidence', () => {
  const result = resolveOpticalRuntime({
    materialRole: 'glz.material.liveGlaze',
    performanceLevel: 'full',
    environmentalResponse: {mode: 'adaptive'},
    platformCapabilities: FULL_LIVE_CAPABILITIES
  });
  assert.equal(result.disposition, 'accepted');
  assert.equal(result.accepted.environmentalResponse.mode, 'adaptive');
  assert.equal(result.accepted.environmentalResponse.localOnly, true);
  assert.equal(result.accepted.environmentalResponse.remoteTransmissionAllowed, false);
  assert.equal(result.accepted.effects.environmentalSampling, true);
  assert.equal(result.accepted.effects.dynamicOpacity, true);
  assert.equal(result.accepted.effects.adaptiveFrost, true);
});

test('adaptive response downgrades to governed static material when required capability evidence is missing', () => {
  const result = resolveOpticalRuntime({
    materialRole: 'glz.material.liveGlaze',
    performanceLevel: 'full',
    environmentalResponse: {mode: 'adaptive'},
    platformCapabilities: BASE_CAPABILITIES
  });
  assert.equal(result.disposition, 'downgraded');
  assert.equal(result.accepted.environmentalResponse.mode, 'static');
  assert.equal(result.accepted.effects.environmentalSampling, false);
  assert.ok(result.fallbacks.includes('governed-static-semantic-material'));
});

test('protected and privacy-restricted surfaces block environmental sampling even when capabilities exist', () => {
  for (const key of ['protectedSurface', 'privacyRestrictedSurface']) {
    const result = resolveOpticalRuntime({
      materialRole: 'glz.material.liveGlaze',
      performanceLevel: 'full',
      environmentalResponse: {mode: 'adaptive', [key]: true},
      platformCapabilities: FULL_LIVE_CAPABILITIES
    });
    assert.equal(result.accepted.environmentalResponse.mode, 'static');
    assert.equal(result.accepted.effects.environmentalSampling, false);
    assert.equal(result.disposition, 'downgraded');
  }
});

test('efficient performance keeps semantic hierarchy while disabling expensive optional optics', () => {
  const result = resolveOpticalRuntime({
    materialRole: 'glz.material.deepGlaze',
    elevationRole: 'glz.elevation.modal',
    performanceLevel: 'efficient',
    platformCapabilities: FULL_LIVE_CAPABILITIES
  });
  assert.equal(result.disposition, 'accepted');
  assert.equal(result.effectiveOpticalProfile, 'deep');
  assert.equal(result.accepted.renderingMode, 'static-glaze');
  assert.equal(result.accepted.effects.backdropBlur, false);
  assert.equal(result.accepted.effects.reflection, false);
  assert.equal(result.accepted.effects.aura, false);
  assert.equal(result.accepted.effects.materialAwareMotion, false);
});

test('reduced motion disables optional motion while preserving rendering continuity', () => {
  const result = resolveOpticalRuntime({
    accessibilityProfile: 'reduced-motion',
    performanceLevel: 'full',
    platformCapabilities: FULL_LIVE_CAPABILITIES
  });
  assert.equal(result.accepted.effects.materialAwareMotion, false);
  assert.equal(result.accepted.effects.connectedTransformation, false);
  assert.ok(result.fallbacks.includes('inherited-v1.3-reduced-motion'));
});

test('unknown semantic request values are explicitly substituted instead of silently accepted', () => {
  const result = resolveOpticalRuntime({
    materialRole: 'glz.material.future',
    elevationRole: 'glz.elevation.future',
    accessibilityProfile: 'future-profile',
    performanceLevel: 'future-performance',
    platformCapabilities: BASE_CAPABILITIES
  });
  assert.equal(result.disposition, 'substituted');
  assert.equal(result.accepted.materialRole, 'glz.material.surface');
  assert.equal(result.accepted.elevationRole, 'glz.elevation.raised');
  assert.equal(result.accepted.accessibilityProfile, 'standard');
  assert.equal(result.accepted.performanceLevel, 'balanced');
});

test('reference web adapter exposes accepted state without claiming external operational authority', () => {
  const properties = new Map();
  const target = {
    dataset: {},
    style: {setProperty(name, value) { properties.set(name, value); }}
  };
  const result = applyOpticalRuntime(target, {
    materialRole: 'glz.material.glaze',
    platformCapabilities: BASE_CAPABILITIES
  });
  assert.equal(target.dataset.glazeV14Disposition, 'accepted');
  assert.equal(target.dataset.glazeV14Rendering, 'optical-glaze');
  assert.equal(properties.get('--glz14-backdrop-blur-enabled'), '1');
  assert.equal(result.accepted.effects.backdropBlur, true);
  assert.equal(opticalRuntimeCandidate.establishesOperationalSecurityAuthority, false);
  assert.equal(opticalRuntimeCandidate.establishesOperationalPrivacyAuthority, false);
});

test('capability adapter is explicit local evidence and never requires telemetry or analytics', () => {
  const resolver = createOpticalRuntimeResolver({
    capabilityAdapter: {resolve() { return BASE_CAPABILITIES; }}
  });
  const result = resolver.resolve({materialRole: 'glz.material.surface'});
  assert.equal(result.disposition, 'accepted');
  assert.equal(resolver.telemetryRequired, false);
  assert.equal(resolver.analyticsRequired, false);
  assert.equal(opticalRuntimeCandidate.telemetryRequired, false);
  assert.equal(opticalRuntimeCandidate.analyticsRequired, false);
});

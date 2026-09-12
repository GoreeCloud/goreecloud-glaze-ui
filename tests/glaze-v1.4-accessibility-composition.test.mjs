import test from 'node:test';
import assert from 'node:assert/strict';

import {
  accessibilityCompositionCandidate,
  resolveAccessibleOpticalRuntime
} from '../js/glaze-v1.4-accessibility-runtime.candidate.mjs';

const FULL_CAPABILITIES = [
  'translucency',
  'backdrop-blur',
  'dynamic-opacity',
  'environmental-sampling',
  'reflection',
  'adaptive-frost',
  'aura',
  'edge-illumination',
  'material-aware-motion',
  'connected-transformation',
  'shadow-diffusion',
  'hdr-aware-luminance'
];

test('standard requests remain backward-compatible with the scalar runtime', () => {
  const result = resolveAccessibleOpticalRuntime({
    materialRole: 'glz.material.glaze',
    accessibilityProfile: 'standard',
    performanceLevel: 'balanced',
    platformCapabilities: ['translucency', 'backdrop-blur']
  });

  assert.equal(result.disposition, 'accepted');
  assert.deepEqual(result.accepted.accessibilityRequirements, []);
  assert.equal(result.accepted.accessibilityProfile, 'standard');
  assert.equal(result.accessibilityComposition.requirementsAreBehaviorAuthority, true);
  assert.equal(result.accessibilityComposition.legacySummaryIsBehaviorAuthority, false);
});

test('simultaneous transparency, forced-colors, motion, and constrained-performance requirements compose', () => {
  const result = resolveAccessibleOpticalRuntime({
    materialRole: 'glz.material.deepGlaze',
    performanceLevel: 'full',
    accessibilityRequirements: [
      'reduced-motion',
      'forced-colors',
      'reduced-transparency',
      'low-power-performance-constrained'
    ],
    platformCapabilities: FULL_CAPABILITIES
  });

  assert.deepEqual(result.accepted.accessibilityRequirements, [
    'reduced-transparency',
    'forced-colors',
    'reduced-motion',
    'low-power-performance-constrained'
  ]);
  assert.equal(result.accepted.accessibilityProfile, 'reduced-transparency');
  assert.equal(result.accepted.performanceLevel, 'efficient');
  assert.equal(result.accepted.renderingMode, 'solid-semantic-surface');
  assert.equal(result.accepted.effects.translucency, false);
  assert.equal(result.accepted.effects.backdropBlur, false);
  assert.equal(result.accepted.effects.reflection, false);
  assert.equal(result.accepted.effects.aura, false);
  assert.equal(result.accepted.effects.edgeIllumination, false);
  assert.equal(result.accepted.effects.materialAwareMotion, false);
  assert.equal(result.accepted.effects.connectedTransformation, false);
  assert.ok(result.fallbacks.includes('system-color-compatible-material'));
  assert.ok(result.fallbacks.includes('inherited-v1.3-reduced-motion'));
  assert.ok(result.reasons.includes('composed-accessibility-requirements-preserved'));
});

test('increased contrast and reduced motion both affect an optical path', () => {
  const result = resolveAccessibleOpticalRuntime({
    accessibilityRequirements: ['increased-contrast', 'reduced-motion'],
    performanceLevel: 'full',
    platformCapabilities: FULL_CAPABILITIES
  });

  assert.equal(result.accepted.accessibilityProfile, 'increased-contrast');
  assert.equal(result.accepted.renderingMode, 'optical-glaze');
  assert.equal(result.accepted.effects.backdropBlur, true);
  assert.equal(result.accepted.effects.reflection, false);
  assert.equal(result.accepted.effects.aura, false);
  assert.equal(result.accepted.effects.edgeIllumination, false);
  assert.equal(result.accepted.effects.materialAwareMotion, false);
  assert.equal(result.accepted.effects.connectedTransformation, false);
});

test('forced-colors remains independent while using increased-contrast legacy summary', () => {
  const result = resolveAccessibleOpticalRuntime({
    accessibilityRequirements: ['forced-colors'],
    performanceLevel: 'full',
    platformCapabilities: FULL_CAPABILITIES
  });

  assert.deepEqual(result.accepted.accessibilityRequirements, ['forced-colors']);
  assert.equal(result.accepted.accessibilityProfile, 'increased-contrast');
  assert.ok(result.reasons.includes('forced-colors-preserved-as-independent-requirement'));
  assert.equal(result.accepted.effects.reflection, false);
});

test('legacy accessibility profile is merged into composable requirements', () => {
  const result = resolveAccessibleOpticalRuntime({
    accessibilityProfile: 'reduced-motion',
    accessibilityRequirements: ['increased-contrast', 'reduced-motion', 'increased-contrast'],
    performanceLevel: 'full',
    platformCapabilities: FULL_CAPABILITIES
  });

  assert.deepEqual(result.accepted.accessibilityRequirements, ['increased-contrast', 'reduced-motion']);
  assert.equal(result.accepted.accessibilityProfile, 'increased-contrast');
  assert.equal(result.accepted.effects.materialAwareMotion, false);
  assert.equal(result.accepted.effects.aura, false);
});

test('unknown accessibility requirements are ignored explicitly and never accepted silently', () => {
  const result = resolveAccessibleOpticalRuntime({
    accessibilityRequirements: ['reduced-motion', 'future-unknown-requirement'],
    platformCapabilities: ['translucency', 'backdrop-blur']
  });

  assert.equal(result.disposition, 'substituted');
  assert.deepEqual(result.accepted.accessibilityRequirements, ['reduced-motion']);
  assert.deepEqual(result.accessibilityComposition.unknownRequirements, ['future-unknown-requirement']);
  assert.ok(result.reasons.some(reason => reason.startsWith('unknown-accessibility-requirements-ignored:')));
});

test('low-power performance requirement constrains the runtime independently of summary precedence', () => {
  const result = resolveAccessibleOpticalRuntime({
    accessibilityRequirements: ['increased-contrast', 'low-power-performance-constrained'],
    performanceLevel: 'full',
    platformCapabilities: FULL_CAPABILITIES
  });

  assert.equal(result.accepted.accessibilityProfile, 'increased-contrast');
  assert.equal(result.accepted.performanceLevel, 'efficient');
  assert.equal(result.accepted.renderingMode, 'static-glaze');
  assert.equal(result.accepted.effects.backdropBlur, false);
  assert.equal(result.accepted.effects.reflection, false);
});

test('candidate metadata remains proposed and non-qualified', () => {
  assert.equal(accessibilityCompositionCandidate.consumerEligible, false);
  assert.equal(accessibilityCompositionCandidate.lifecycleAuthority, false);
  assert.equal(accessibilityCompositionCandidate.simultaneousRequirementsPreserved, true);
  assert.equal(accessibilityCompositionCandidate.requirementsAreBehaviorAuthority, true);
  assert.equal(accessibilityCompositionCandidate.legacySummaryIsBehaviorAuthority, false);
  assert.equal(accessibilityCompositionCandidate.browserMatrixQualificationEstablished, false);
  assert.equal(accessibilityCompositionCandidate.assistiveTechnologyQualificationEstablished, false);
  assert.equal(accessibilityCompositionCandidate.physicalDeviceQualificationEstablished, false);
  assert.equal(accessibilityCompositionCandidate.productionPerformanceQualificationEstablished, false);
});

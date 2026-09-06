import assert from 'node:assert/strict';
import test from 'node:test';

import {
  applyTypography,
  resolveTypography,
  resolveTypographyEnvironment,
  responsiveTypographyCandidate
} from '../js/glaze-v1.3-typography.candidate.mjs';

const variableAxes = Object.freeze({
  wght: {min: 300, max: 750, default: 400},
  wdth: {min: 90, max: 110, default: 100},
  opsz: {min: 12, max: 72, default: 16},
  GRAD: {min: -50, max: 50, default: 0}
});

test('unknown role falls back to semantic body typography', () => {
  const result = resolveTypography('unknown-role', {environment: 'compact'});
  assert.equal(result.role, 'body');
  assert.equal(result.fontSize, '1rem');
  assert.equal(result.fontWeight, 400);
});

test('unknown environment falls back to medium rather than arbitrary scaling', () => {
  const result = resolveTypography('title', {environment: 'unknown-environment'});
  assert.equal(result.environment, 'medium');
  assert.equal(result.fontSize, '1.75rem');
});

test('environment matrix is semantic and not one uniform scale factor', () => {
  const compact = resolveTypographyEnvironment('compact');
  const workspace = resolveTypographyEnvironment('workspace');
  const farView = resolveTypographyEnvironment('farView');
  assert.equal(compact.uniformScaleOnly, false);
  assert.equal(workspace.roleSizeRem.body, 1);
  assert.equal(workspace.roleSizeRem.caption, 0.75);
  assert.equal(farView.roleSizeRem.body, 1.5);
  assert.equal(farView.roleSizeRem.label, 1.25);
  assert.notEqual(farView.roleSizeRem.body / workspace.roleSizeRem.body, farView.roleSizeRem.display / workspace.roleSizeRem.display);
});

test('far-view and wearable retain explicit readable role values', () => {
  assert.equal(resolveTypography('body', {environment: 'far-view'}).fontSize, '1.5rem');
  assert.equal(resolveTypography('label', {environment: 'farView'}).fontSize, '1.25rem');
  assert.equal(resolveTypography('body', {environment: 'wearable'}).fontSize, '1rem');
  assert.equal(resolveTypography('caption', {environment: 'wearable'}).fontSize, '0.8125rem');
});

test('numeric role preserves tabular lining figures', () => {
  const result = resolveTypography('numeral', {environment: 'expanded'});
  assert.equal(result.fontVariantNumeric, 'tabular-nums lining-nums');
  assert.equal(result.fontSize, '2.25rem');
});

test('variable axes are omitted when the active local font declares no capabilities', () => {
  const result = resolveTypography('title', {state: 'selected', expression: 'expressive'});
  assert.deepEqual(result.variableAxesApplied, {});
  assert.equal(result.fontVariationSettings, 'normal');
  assert.equal(result.semanticRolePreserved, true);
});

test('declared variable axes receive bounded semantic requests', () => {
  const result = resolveTypography('title', {
    environment: 'medium',
    state: 'selected',
    expression: 'balanced',
    axisCapabilities: variableAxes
  });
  assert.equal(result.variableAxesApplied.wght, 650);
  assert.equal(result.variableAxesApplied.opsz, 28);
  assert.equal(result.variableAxesApplied.GRAD, 20);
  assert.equal(result.widthCompressionApplied, false);
  assert.match(result.fontVariationSettings, /"wght" 650/);
  assert.match(result.fontVariationSettings, /"GRAD" 20/);
});

test('axis requests clamp to adapter-declared font capability ranges', () => {
  const result = resolveTypography('display', {
    environment: 'farView',
    state: 'selected',
    expression: 'expressive',
    axisCapabilities: {
      wght: {min: 400, max: 625, default: 500},
      opsz: {min: 10, max: 60, default: 16},
      GRAD: {min: -10, max: 15, default: 0}
    }
  });
  assert.equal(result.variableAxesApplied.wght, 625);
  assert.equal(result.variableAxesApplied.opsz, 60);
  assert.equal(result.variableAxesApplied.GRAD, 15);
});

test('compressed state uses width only when declared and accessibility permits it', () => {
  const normal = resolveTypography('label', {
    state: 'compressed',
    expression: 'balanced',
    axisCapabilities: variableAxes
  });
  const large = resolveTypography('label', {
    state: 'compressed',
    expression: 'balanced',
    textScale: 2,
    axisCapabilities: variableAxes
  });
  assert.equal(normal.variableAxesApplied.wdth, 96);
  assert.equal(normal.widthCompressionApplied, true);
  assert.equal(large.variableAxesApplied.wdth, undefined);
  assert.equal(large.widthCompressionApplied, false);
  assert.equal(large.largeText, true);
  assert.equal(large.fontSize, '1.75rem');
});

test('large text scales semantic size instead of being counteracted by expression', () => {
  const result = resolveTypography('body', {
    environment: 'compact',
    textScale: 2,
    state: 'selected',
    expression: 'expressive',
    axisCapabilities: variableAxes
  });
  assert.equal(result.fontSize, '2rem');
  assert.equal(result.largeText, true);
  assert.equal(result.widthCompressionApplied, false);
  assert.equal(result.semanticRolePreserved, true);
});

test('static-font fallback keeps restrained state emphasis without variable font dependency', () => {
  const calm = resolveTypography('body', {state: 'selected', expression: 'calm'});
  const balanced = resolveTypography('body', {state: 'selected', expression: 'balanced'});
  assert.equal(calm.fontWeight, 400);
  assert.equal(balanced.fontWeight, 500);
  assert.equal(balanced.fontVariationSettings, 'normal');
});

test('applyTypography writes semantic data and deterministic CSS values', () => {
  const properties = new Map();
  const target = {
    dataset: {},
    style: {setProperty(name, value) { properties.set(name, value); }}
  };
  const result = applyTypography(target, 'heading', {
    environment: 'expanded',
    expression: 'expressive',
    state: 'current',
    axisCapabilities: variableAxes
  });
  assert.equal(target.dataset.glazeTypeV13, 'heading');
  assert.equal(target.dataset.glazeTypeEnvironment, 'expanded');
  assert.equal(target.dataset.glazeExpression, 'expressive');
  assert.equal(properties.get('font-size'), '1.5rem');
  assert.equal(properties.get('--glz13-type-weight'), String(result.fontWeight));
  assert.match(properties.get('font-variation-settings'), /"wght"/);
});

test('candidate metadata preserves lifecycle and evidence boundaries', () => {
  assert.equal(responsiveTypographyCandidate.releaseLifecycle, 'proposed');
  assert.equal(responsiveTypographyCandidate.consumerEligible, false);
  assert.equal(responsiveTypographyCandidate.remoteRuntimeFontDependencyAllowed, false);
  assert.equal(responsiveTypographyCandidate.continuousAutonomousAxisAnimationAllowed, false);
  assert.equal(responsiveTypographyCandidate.accessibilityOutranksExpression, true);
  assert.equal(responsiveTypographyCandidate.humanReadabilityAcceptanceEstablished, false);
});

import test from 'node:test';
import assert from 'node:assert/strict';

import {
  COLOR_AUTHORITY_PRECEDENCE,
  DEFAULT_GLAZE_ACCENT,
  contextRoleAllowed,
  contrastRatio,
  deriveAccentPalette,
  deriveContextAccent,
  dynamicColorCandidate,
  normalizeAccentSeed,
  resolveColorValue
} from '../js/glaze-v1.3-dynamic-color.candidate.mjs';

const HEX = /^#[0-9A-F]{6}$/;

test('normalizes valid local accent seeds and falls back deterministically', () => {
  assert.equal(normalizeAccentSeed('#abc'), '#AABBCC');
  assert.equal(normalizeAccentSeed({r: 104, g: 174, b: 224}), DEFAULT_GLAZE_ACCENT);
  assert.equal(normalizeAccentSeed('not-a-color'), DEFAULT_GLAZE_ACCENT);
  assert.equal(normalizeAccentSeed(null), DEFAULT_GLAZE_ACCENT);
});

test('derives a complete deterministic accent family for every appearance', () => {
  for (const appearance of ['light', 'dark', 'deep-dark']) {
    const first = deriveAccentPalette('#7A4BE8', {appearance});
    const second = deriveAccentPalette('#7A4BE8', {appearance});

    assert.deepEqual(first, second);
    assert.equal(first.appearance, appearance);
    assert.equal(first.perceptualModel, 'OKLCH');

    for (const role of [
      'primary',
      'secondary',
      'tertiary',
      'subtleContainer',
      'highEmphasisContainer',
      'onAccent',
      'focus',
      'selection'
    ]) {
      assert.match(first.roles[role], HEX, `${appearance}:${role}`);
    }

    assert.ok(
      first.validation.onAccentContrast >= first.validation.onAccentMinimum,
      `${appearance} on-accent contrast ${first.validation.onAccentContrast}`
    );
    assert.ok(
      first.validation.focusContrast >= first.validation.focusMinimum,
      `${appearance} focus contrast ${first.validation.focusContrast}`
    );
    assert.equal(first.validation.colorOnlyStateAllowed, false);
  }
});

test('invalid or absent personalization still yields a complete default Glaze theme', () => {
  const invalid = deriveAccentPalette('invalid', {appearance: 'light'});
  const missing = deriveAccentPalette(null, {appearance: 'light'});
  const explicit = deriveAccentPalette(DEFAULT_GLAZE_ACCENT, {appearance: 'light'});

  assert.deepEqual(invalid.roles, explicit.roles);
  assert.deepEqual(missing.roles, explicit.roles);
  assert.equal(missing.source, 'default-glaze-accent');
});

test('contrast helper is symmetric and reports accessible black/white extremes', () => {
  assert.equal(contrastRatio('#000000', '#FFFFFF'), contrastRatio('#FFFFFF', '#000000'));
  assert.ok(contrastRatio('#000000', '#FFFFFF') > 20);
});

test('derives bounded local context accents without network or telemetry authority', () => {
  const context = deriveContextAccent({r: 255, g: 0, b: 255}, {appearance: 'dark'});
  assert.ok(context);
  assert.match(context.color, HEX);
  assert.equal(context.source, 'producer-supplied-local-color-summary');
  assert.equal(context.perceptualModel, 'OKLCH');
  assert.equal(context.maximumChroma, 0.1);
  assert.equal(context.networkRequired, false);
  assert.equal(context.telemetryAuthorized, false);
  assert.equal(deriveContextAccent('invalid'), null);
});

test('context influence is explicitly bounded away from semantic truth', () => {
  for (const role of ['accent', 'progress', 'control', 'live-glaze', 'local-highlight']) {
    assert.equal(contextRoleAllowed(role), true, role);
  }
  for (const role of ['success', 'warning', 'danger', 'protected', 'offline', 'security-status']) {
    assert.equal(contextRoleAllowed(role), false, role);
  }
});

test('authority precedence follows the V1.3 governing order', () => {
  assert.deepEqual(COLOR_AUTHORITY_PRECEDENCE, [
    'accessibility',
    'semantic',
    'product-identity',
    'user-accent',
    'context-accent',
    'default-glaze-accent'
  ]);

  const all = {
    accessibility: {accent: '#111111'},
    semantic: {accent: '#222222'},
    productIdentity: {accent: '#333333'},
    userAccent: {accent: '#444444'},
    contextAccent: {accent: '#555555'},
    defaultAccent: {accent: '#666666'}
  };
  assert.deepEqual(resolveColorValue('accent', all), {
    value: '#111111',
    authority: 'accessibility',
    protectedRole: false
  });

  delete all.accessibility;
  assert.equal(resolveColorValue('accent', all).authority, 'semantic');
  delete all.semantic;
  assert.equal(resolveColorValue('accent', all).authority, 'product-identity');
  delete all.productIdentity;
  assert.equal(resolveColorValue('accent', all).authority, 'user-accent');
  delete all.userAccent;
  assert.equal(resolveColorValue('accent', all).authority, 'context-accent');
  delete all.contextAccent;
  assert.equal(resolveColorValue('accent', all).authority, 'default-glaze-accent');
});

test('protected semantic roles cannot be manufactured by brand, user, or context color', () => {
  const protectedWithoutTruth = resolveColorValue('danger', {
    productIdentity: {danger: '#123456'},
    userAccent: {danger: '#234567'},
    contextAccent: {danger: '#345678'},
    defaultAccent: {danger: '#456789'}
  });
  assert.deepEqual(protectedWithoutTruth, {
    value: null,
    authority: null,
    protectedRole: true
  });

  const semanticTruth = resolveColorValue('danger', {
    semantic: {danger: '#C62828'},
    userAccent: {danger: '#00FF00'}
  });
  assert.deepEqual(semanticTruth, {
    value: '#C62828',
    authority: 'semantic',
    protectedRole: true
  });

  const accessibilityOverride = resolveColorValue('danger', {
    accessibility: {danger: 'CanvasText'},
    semantic: {danger: '#C62828'}
  });
  assert.deepEqual(accessibilityOverride, {
    value: 'CanvasText',
    authority: 'accessibility',
    protectedRole: true
  });
});

test('runtime metadata preserves Proposed and local-first boundaries', () => {
  assert.equal(dynamicColorCandidate.targetVersion, '1.3.0-candidate');
  assert.equal(dynamicColorCandidate.releaseLifecycle, 'proposed');
  assert.equal(dynamicColorCandidate.consumerEligible, false);
  assert.equal(dynamicColorCandidate.lifecycleAuthority, false);
  assert.equal(dynamicColorCandidate.perceptualModel, 'OKLCH');
  assert.equal(dynamicColorCandidate.dependencyFree, true);
  assert.equal(dynamicColorCandidate.networkRequired, false);
  assert.equal(dynamicColorCandidate.telemetryAuthorized, false);
});

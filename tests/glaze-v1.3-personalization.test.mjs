import test from 'node:test';
import assert from 'node:assert/strict';

import {
  DEFAULT_PERSONALIZATION,
  PERSONALIZATION_CONTINUITY,
  createPersonalizationController,
  deriveWallpaperAtmosphere,
  deserializePersonalization,
  normalizePersonalization,
  personalizationCandidate,
  resolveAppearance,
  resolvePersonalization,
  serializePersonalization
} from '../js/glaze-v1.3-personalization.candidate.mjs';

test('normalization fails closed to governed defaults', () => {
  const value = normalizePersonalization({appearance: 'neon', density: 'tiny', materialClarity: 'fog'});
  assert.equal(value.appearance, 'follow-system');
  assert.equal(value.density, 'standard');
  assert.equal(value.materialClarity, 'balanced');
  assert.equal(value.accentSeed, '#68AEE0');
});

test('legacy atmosphere maps into the bounded expression profile', () => {
  assert.equal(normalizePersonalization({atmosphere: 'calm'}).expressionProfile, 'calm');
  assert.equal(normalizePersonalization({atmosphere: 'wild'}).expressionProfile, 'balanced');
});

test('follow-system delegates to a consumer system adapter', () => {
  assert.equal(resolveAppearance('follow-system', {resolve: () => 'deep-dark'}), 'deep-dark');
  assert.equal(resolveAppearance('follow-system', {resolve: () => 'unsupported'}), 'light');
});

test('manual appearance does not depend on system resolution', () => {
  assert.equal(resolveAppearance('dark', {resolve: () => 'light'}), 'dark');
});

test('user accent is routed through governed Dynamic Color derivation', () => {
  const resolved = resolvePersonalization({appearance: 'dark', accentSeed: '#ff0000'});
  assert.equal(resolved.accentPalette.seed, '#FF0000');
  assert.equal(resolved.accentPalette.appearance, 'dark');
  assert.equal(resolved.semanticColorRemappingAllowed, false);
  assert.equal(resolved.productIdentityReplacementAllowed, false);
});

test('expression profile selects bounded typography profile and shape ceiling', () => {
  const calm = resolvePersonalization({expressionProfile: 'calm'});
  const expressive = resolvePersonalization({expressionProfile: 'expressive'});
  assert.equal(calm.typographyExpressionProfile, 'calm');
  assert.equal(calm.shapeExpressionCeiling, 'soft');
  assert.equal(expressive.typographyExpressionProfile, 'expressive');
  assert.equal(expressive.shapeExpressionCeiling, 'expressive');
  assert.equal(expressive.arbitraryComponentGeometryAllowed, false);
});

test('wallpaper atmosphere uses only bounded producer-supplied RGB summaries', () => {
  const derived = deriveWallpaperAtmosphere({r: 250, g: 40, b: 80}, {expressionProfile: 'expressive'});
  assert.equal(derived.source, 'producer-supplied-local-rgb-summary');
  assert.ok(derived.alpha <= 0.12);
  assert.ok(derived.chromaRetention <= 0.28);
  assert.equal(derived.networkRequired, false);
  assert.equal(derived.rawWallpaperPixelsRequired, false);
  assert.equal(deriveWallpaperAtmosphere('raw-image'), null);
});

test('Reduced Transparency and Forced Colors disable wallpaper atmosphere and force solid clarity', () => {
  for (const context of [{reducedTransparency: true}, {forcedColors: true}]) {
    const resolved = resolvePersonalization(
      {materialClarity: 'clear', wallpaperAtmosphere: true},
      {...context, wallpaperRgbSummary: {r: 20, g: 100, b: 200}}
    );
    assert.equal(resolved.materialClarity, 'solid');
    assert.equal(resolved.wallpaperAtmosphere, null);
  }
});

test('large text relaxes productive density before harming reflow', () => {
  const resolved = resolvePersonalization({density: 'productive'}, {textScalePercent: 200});
  assert.equal(resolved.accessibility.reflowRequired, true);
  assert.equal(resolved.density, 'standard');
});

test('Touch Assistance resolves comfortable density and 56px target floor', () => {
  const resolved = resolvePersonalization({density: 'immersive'}, {touchAssistance: true});
  assert.equal(resolved.density, 'comfortable');
  assert.equal(resolved.accessibility.targetFloorPx, 56);
});

test('preference envelopes round-trip and malformed envelopes fail closed', () => {
  const encoded = serializePersonalization({appearance: 'deep-dark', expressionProfile: 'calm'});
  const decoded = deserializePersonalization(encoded);
  assert.equal(decoded.appearance, 'deep-dark');
  assert.equal(decoded.expressionProfile, 'calm');
  assert.equal(deserializePersonalization('{bad json'), null);
  assert.equal(deserializePersonalization({schemaVersion: 99, preferences: {}}), null);
});

test('controller persistence remains optional and consumer-owned', () => {
  let stored = null;
  const adapter = {
    load: () => stored,
    save: value => { stored = value; },
    clear: () => { stored = null; }
  };
  const controller = createPersonalizationController({persistenceAdapter: adapter});
  assert.equal(controller.persistenceEnabled, true);
  controller.set({appearance: 'dark'}, {persist: true});
  assert.ok(stored.includes('"appearance":"dark"'));
  controller.clearPersisted();
  assert.equal(stored, null);
});

test('personalization preserves continuity and does not claim native or sync acceptance', () => {
  assert.ok(PERSONALIZATION_CONTINUITY.includes('unsaved-work'));
  assert.ok(PERSONALIZATION_CONTINUITY.includes('product-identity'));
  assert.equal(personalizationCandidate.directCrossDeviceSyncImplemented, false);
  assert.equal(personalizationCandidate.directWallpaperPixelAcquisitionImplemented, false);
  assert.equal(personalizationCandidate.nativeAdapterAcceptanceEstablished, false);
  assert.equal(DEFAULT_PERSONALIZATION.wallpaperAtmosphere, true);
});

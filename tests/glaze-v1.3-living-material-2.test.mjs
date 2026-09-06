import assert from 'node:assert/strict';
import test from 'node:test';

import {
  applyLivingMaterial2,
  createGlazePerformanceGovernor,
  livingMaterial2Candidate,
  resolveGlazePerformanceTier,
  resolveLivingMaterial2
} from '../js/glaze-v1.3-living-material-2.candidate.mjs';

test('ordinary Glaze is capped at Responsive Glaze while Live Glaze may use Tier 3', () => {
  const ordinary = resolveLivingMaterial2({role: 'glaze', requestedTier: 3});
  const live = resolveLivingMaterial2({role: 'live-glaze', requestedTier: 3});
  assert.equal(ordinary.tier, 2);
  assert.equal(ordinary.tierName, 'responsive-glaze');
  assert.equal(live.tier, 3);
  assert.equal(live.tierName, 'living-glaze');
});

test('pressed response is tactile but bounded and subtle', () => {
  const pressed = resolveLivingMaterial2({role: 'live-glaze', state: 'pressed', requestedTier: 3});
  assert.ok(pressed.scale < 1);
  assert.ok(pressed.scale >= 0.98);
  assert.ok(pressed.opticalDensity > 0);
  assert.ok(pressed.specular >= 0 && pressed.specular <= 1);
});

test('accessibility may force Solid without sacrificing semantic object presence', () => {
  const forced = resolveLivingMaterial2({role: 'live-glaze', accessibility: {forcedColors: true}});
  const reduced = resolveLivingMaterial2({role: 'live-glaze', accessibility: {reducedTransparency: true}});
  assert.equal(forced.tier, 0);
  assert.equal(reduced.tier, 0);
  assert.equal(forced.scale, 1);
  assert.equal(forced.specular, 0);
  assert.equal(reduced.transmission, null);
});

test('qualitative performance signals degrade effects conservatively', () => {
  assert.equal(resolveGlazePerformanceTier({signals: {frameTiming: 'critical'}}).tier, 0);
  assert.equal(resolveGlazePerformanceTier({signals: {compositorCapability: 'none'}}).tier, 0);
  assert.equal(resolveGlazePerformanceTier({signals: {renderingCapability: 'limited'}}).tier, 1);
  assert.equal(resolveGlazePerformanceTier({signals: {frameTiming: 'strained'}}).tier, 1);
  assert.equal(resolveGlazePerformanceTier({signals: {powerSaving: 'on'}}).tier, 1);
  assert.equal(resolveGlazePerformanceTier({signals: {compositorCapability: 'partial'}}).tier, 2);
  assert.equal(resolveGlazePerformanceTier({signals: {glazeRegionLoad: 'high'}}).tier, 2);
});

test('performance governor never upgrades above requested material tier', () => {
  assert.equal(resolveGlazePerformanceTier({requestedTier: 1, signals: {frameTiming: 'healthy'}}).tier, 1);
  assert.equal(resolveGlazePerformanceTier({requestedTier: 0, signals: {renderingCapability: 'high'}}).tier, 0);
});

test('reduced motion removes connected material motion and press scaling', () => {
  const material = resolveLivingMaterial2({
    role: 'live-glaze',
    state: 'pressed',
    requestedTier: 3,
    accessibility: {reducedMotion: true}
  });
  assert.equal(material.scale, 1);
  assert.equal(material.connectedMaterialMotionAllowed, false);
});

test('environmental transmission requires Live Glaze Tier 3 and dynamic-color authority', () => {
  const allowed = resolveLivingMaterial2({
    role: 'live-glaze',
    requestedTier: 3,
    transmission: {authority: 'dynamic-color', css: 'oklch(70% 0.08 230 / 0.08)'}
  });
  assert.equal(allowed.transmission?.authority, 'dynamic-color');
  assert.equal(allowed.transmission?.materialColorRemainsNeutral, true);
  assert.equal(allowed.transmission?.maxInfluence, 0.10);

  const wrongAuthority = resolveLivingMaterial2({
    role: 'live-glaze',
    requestedTier: 3,
    transmission: {authority: 'arbitrary-theme', css: 'red'}
  });
  assert.equal(wrongAuthority.transmission, null);

  const ordinary = resolveLivingMaterial2({
    role: 'glaze',
    requestedTier: 3,
    transmission: {authority: 'dynamic-color', css: 'oklch(70% 0.08 230 / 0.08)'}
  });
  assert.equal(ordinary.transmission, null);
});

test('geometry-aware specular response remains bounded and focus-limited', () => {
  const top = resolveLivingMaterial2({
    role: 'live-glaze',
    state: 'hover',
    edgeOrientation: 'top',
    appearance: 'deep-dark',
    interactionVelocity: 'fast'
  });
  assert.ok(top.specular > 0);
  assert.ok(top.specular <= 1);

  const focus = resolveLivingMaterial2({
    role: 'live-glaze',
    state: 'focus',
    edgeOrientation: 'top',
    appearance: 'deep-dark'
  });
  assert.ok(focus.specular <= 0.62);
});

test('complex/bright backdrops increase optical density only within bounded adaptive tiers', () => {
  const base = resolveLivingMaterial2({role: 'live-glaze', underlyingComplexity: 'simple', underlyingLuminance: 'dark'});
  const complex = resolveLivingMaterial2({role: 'live-glaze', underlyingComplexity: 'complex', underlyingLuminance: 'bright'});
  assert.ok(complex.opticalDensity > base.opticalDensity);
  assert.ok(complex.opticalDensity <= 1);
});

test('unknown and malformed inputs fall back deterministically', () => {
  const material = resolveLivingMaterial2({
    role: 'not-a-role',
    state: 'not-a-state',
    appearance: 'not-an-appearance',
    requestedTier: 99,
    performanceSignals: {frameTiming: 'made-up'}
  });
  assert.equal(material.role, 'glaze');
  assert.equal(material.state, 'rest');
  assert.equal(material.appearance, 'light');
  assert.equal(material.governor.signals.frameTiming, 'unknown');
});

test('applyLivingMaterial2 emits deterministic dataset and CSS custom properties', () => {
  const properties = new Map();
  const target = {
    dataset: {},
    style: {setProperty(name, value) { properties.set(name, value); }}
  };
  const result = applyLivingMaterial2(target, {role: 'deep-glaze', state: 'pressed'});
  assert.equal(target.dataset.glazeMaterialV13, 'deep-glaze');
  assert.equal(target.dataset.glazeMaterialState, 'pressed');
  assert.equal(target.dataset.glazeTier, String(result.tier));
  assert.equal(properties.get('--glz13-material-scale'), String(result.scale));
  assert.equal(properties.get('--glz13-material-transmission'), 'transparent');
});

test('governor adapter stays local and declares no telemetry or analytics requirement', () => {
  const governor = createGlazePerformanceGovernor({
    signalAdapter: {resolve: () => ({powerSaving: 'on'})}
  });
  assert.equal(governor.kind, 'glaze-performance-governor-v1.3');
  assert.equal(governor.telemetryRequired, false);
  assert.equal(governor.analyticsRequired, false);
  assert.equal(governor.resolve().tier, 1);
});

test('candidate metadata preserves Proposed and non-consumer boundary', () => {
  assert.equal(livingMaterial2Candidate.targetVersion, '1.3.0-candidate');
  assert.equal(livingMaterial2Candidate.releaseLifecycle, 'proposed');
  assert.equal(livingMaterial2Candidate.consumerEligible, false);
  assert.equal(livingMaterial2Candidate.productionPerformanceThresholdsEstablished, false);
  assert.equal(livingMaterial2Candidate.telemetryRequired, false);
  assert.equal(livingMaterial2Candidate.materialColorDistinctFromTransmittedColor, true);
});

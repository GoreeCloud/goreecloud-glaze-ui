import assert from 'node:assert/strict';
import test from 'node:test';

import {
  applyConcentricChild,
  applyShape,
  canMorphShape,
  expressiveShapeCandidate,
  resolveConcentricCorners,
  resolveConcentricRadius,
  resolveShape,
  resolveShapeMorph
} from '../js/glaze-v1.3-shape.candidate.mjs';

test('semantic roles inherit calm baseline geometry', () => {
  assert.deepEqual(resolveShape('quiet').cornersPx, [10, 10, 10, 10]);
  assert.deepEqual(resolveShape('soft').cornersPx, [20, 20, 20, 20]);
  assert.deepEqual(resolveShape('rounded').cornersPx, [24, 24, 24, 24]);
});

test('capsule resolves from control size when dimensions are available', () => {
  const shape = resolveShape('capsule', {widthPx: 160, heightPx: 48});
  assert.deepEqual(shape.cornersPx, [24, 24, 24, 24]);
  assert.equal(shape.expressive, false);
});

test('capsule retains semantic sentinel when dimensions are unavailable', () => {
  assert.deepEqual(resolveShape('capsule').cornersPx, [999, 999, 999, 999]);
});

test('expressive and hero profiles are bounded controlled curvature', () => {
  const expressive = resolveShape('expressive', {profile: 'resonant'});
  const hero = resolveShape('hero', {profile: 'orbit'});
  assert.equal(expressive.profile, 'resonant');
  assert.equal(hero.profile, 'orbit');
  assert.ok(Math.min(...expressive.cornersPx) >= 26 * 0.6);
  assert.ok(Math.max(...expressive.cornersPx) <= 26);
  assert.ok(Math.min(...hero.cornersPx) >= 28 * 0.6);
  assert.equal(hero.hero, true);
});

test('unknown role falls back to Soft rather than arbitrary geometry', () => {
  const shape = resolveShape('unknown-shape');
  assert.equal(shape.role, 'soft');
  assert.deepEqual(shape.cornersPx, [20, 20, 20, 20]);
});

test('concentric radius follows governed reference formula', () => {
  assert.equal(resolveConcentricRadius(24, 6, 0), 18);
  assert.equal(resolveConcentricRadius(24, 6, 1.5), 19.5);
  assert.equal(resolveConcentricRadius(4, 10, 0), 0);
  assert.deepEqual(resolveConcentricCorners([24, 20, 16, 12], 4, 1), [21, 17, 13, 9]);
});

test('concentric corner input rejects arbitrary incomplete geometry', () => {
  assert.throws(() => resolveConcentricCorners([20, 20], 4), /four radius values/);
});

test('morph compatibility is semantic and bounded', () => {
  assert.equal(canMorphShape('soft', 'rounded'), true);
  assert.equal(canMorphShape('rounded', 'expressive'), true);
  assert.equal(canMorphShape('hero', 'quiet'), false);
  assert.throws(() => resolveShapeMorph('hero', 'quiet'), /Incompatible semantic shape morph/);
});

test('compatible morph interpolates shape without changing semantic continuity requirement', () => {
  const morph = resolveShapeMorph('rounded', 'expressive', {
    progress: 0.5,
    from: {baseRadiusPx: 24},
    to: {baseRadiusPx: 26, profile: 'resonant'}
  });
  assert.equal(morph.from, 'rounded');
  assert.equal(morph.to, 'expressive');
  assert.equal(morph.progress, 0.5);
  assert.equal(morph.semanticContinuityRequired, true);
  assert.equal(morph.autonomousDecorativeMorph, false);
});

test('reduced motion makes morph geometry immediate rather than continuously animated', () => {
  const start = resolveShapeMorph('soft', 'rounded', {progress: 0.5, reducedMotion: true});
  const end = resolveShapeMorph('soft', 'rounded', {progress: 1, reducedMotion: true});
  assert.equal(start.progress, 0);
  assert.equal(end.progress, 1);
});

test('applyShape writes semantic role and governed radius', () => {
  const properties = new Map();
  const target = {dataset: {}, style: {setProperty(name, value) { properties.set(name, value); }}};
  const shape = applyShape(target, 'expressive', {profile: 'sweep'});
  assert.equal(target.dataset.glazeShapeV13, 'expressive');
  assert.equal(target.dataset.glazeShapeProfile, 'sweep');
  assert.equal(properties.get('--glz13-shape-radius'), shape.cssBorderRadius);
});

test('applyConcentricChild writes derived child radius only', () => {
  const properties = new Map();
  const target = {style: {setProperty(name, value) { properties.set(name, value); }}};
  const result = applyConcentricChild(target, [28, 28, 24, 24], 6, 0);
  assert.deepEqual(result.cornersPx, [22, 22, 18, 18]);
  assert.equal(properties.get('--glz13-concentric-radius'), result.cssBorderRadius);
});

test('candidate metadata keeps optical and lifecycle qualification separate', () => {
  assert.equal(expressiveShapeCandidate.releaseLifecycle, 'proposed');
  assert.equal(expressiveShapeCandidate.consumerEligible, false);
  assert.equal(expressiveShapeCandidate.continuousDecorativeMorphingAllowed, false);
  assert.equal(expressiveShapeCandidate.humanOpticalAcceptanceEstablished, false);
});

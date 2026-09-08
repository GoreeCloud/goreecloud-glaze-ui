import assert from 'node:assert/strict';
import test from 'node:test';

import {
  applyMotionSemantics,
  motionContinuityCandidate,
  resolveConnectedTransformation,
  resolveDirectManipulation,
  resolveMotion
} from '../js/glaze-v1.3-motion.candidate.mjs';

test('ordinary connected motion uses deliberate family rather than rare spatial timing', () => {
  const connected = resolveMotion('connected');
  const spatial = resolveMotion('spatial', {relationshipJustified: true});
  assert.equal(connected.durationMs, 360);
  assert.equal(spatial.durationMs, 480);
  assert.ok(connected.durationMs < spatial.durationMs);
});

test('spatial motion falls back unless relationship is explicitly justified', () => {
  const result = resolveMotion('spatial');
  assert.equal(result.requestedRole, 'spatial');
  assert.equal(result.role, 'connected');
  assert.equal(result.spatialFallbackApplied, true);
  assert.equal(result.durationMs, 360);
});

test('motion state and focus never wait for animation completion', () => {
  for (const role of ['micro', 'standard', 'connected', 'expressive', 'spatial']) {
    const result = resolveMotion(role, {relationshipJustified: role === 'spatial'});
    assert.equal(result.stateCommitWaitsForAnimation, false);
    assert.equal(result.focusWaitsForAnimation, false);
    assert.equal(result.taskCompletionMayBeDelayedByMotion, false);
  }
});

test('Reduced Motion removes nonessential travel and duration', () => {
  const result = resolveMotion('connected', {reducedMotion: true});
  assert.equal(result.profile, 'minimal');
  assert.equal(result.durationMs, 0);
  assert.equal(result.distancePx, 0);
  assert.equal(result.stateCommitWaitsForAnimation, false);
});

test('explicit reduced profile preserves bounded timing while removing travel', () => {
  const result = resolveMotion('connected', {profile: 'reduced'});
  assert.equal(result.profile, 'reduced');
  assert.equal(result.durationMs, 270);
  assert.equal(result.distancePx, 0);
});

test('direct manipulation remains immediate and interruptible', () => {
  const result = resolveDirectManipulation({reducedMotion: true});
  assert.equal(result.trackingDurationMs, 0);
  assert.equal(result.tracksInputImmediately, true);
  assert.equal(result.userMayInterrupt, true);
  assert.equal(result.settleBlocksStateChange, false);
  assert.equal(result.reducedMotionStillTracksInput, true);
});

test('known connected transformation preserves identity and continuity', () => {
  const result = resolveConnectedTransformation('search-capsule-to-search-panel');
  assert.equal(result.knownRelationship, true);
  assert.equal(result.connectedIdentityUsed, true);
  assert.equal(result.semanticIdentityPreserved, true);
  assert.equal(result.currentTaskPreserved, true);
  assert.equal(result.typedInputPreserved, true);
  assert.equal(result.unsavedWorkPreserved, true);
  assert.equal(result.pageReloadRequired, false);
  assert.equal(result.motion.role, 'connected');
});

test('unknown relationship uses a standard transition instead of inventing a morph', () => {
  const result = resolveConnectedTransformation('unknown-relationship');
  assert.equal(result.knownRelationship, false);
  assert.equal(result.connectedIdentityUsed, false);
  assert.equal(result.motion.role, 'standard');
  assert.equal(result.semanticIdentityPreserved, true);
});

test('large spatial connected transformation requires explicit known relationship', () => {
  const known = resolveConnectedTransformation('thumbnail-to-detail', {largeSpatialJustified: true});
  const unknown = resolveConnectedTransformation('unknown', {largeSpatialJustified: true});
  assert.equal(known.motion.role, 'spatial');
  assert.equal(known.motion.relationshipJustified, true);
  assert.equal(unknown.motion.role, 'standard');
});

test('no spring runtime or continuous autonomous motion is introduced', () => {
  const result = resolveMotion('expressive');
  assert.equal(result.newSpringRuntimeUsed, false);
  assert.equal(result.continuousAutonomousMotion, false);
  assert.equal(result.userDrivenMotionInterruptible, true);
});

test('applyMotionSemantics writes bounded semantic CSS variables', () => {
  const properties = new Map();
  const target = {
    dataset: {},
    style: {setProperty(name, value) { properties.set(name, value); }}
  };
  const result = applyMotionSemantics(target, 'connected');
  assert.equal(target.dataset.glazeMotionV13, 'connected');
  assert.equal(target.dataset.glazeMotionProfile, 'full');
  assert.equal(properties.get('--glz13-motion-duration'), '360ms');
  assert.equal(properties.get('--glz13-motion-distance'), '16px');
  assert.equal(result.stateCommitWaitsForAnimation, false);
});

test('candidate metadata preserves lifecycle and physical acceptance boundaries', () => {
  assert.equal(motionContinuityCandidate.releaseLifecycle, 'proposed');
  assert.equal(motionContinuityCandidate.consumerEligible, false);
  assert.equal(motionContinuityCandidate.stateIndependentOfAnimationCompletion, true);
  assert.equal(motionContinuityCandidate.focusIndependentOfAnimationCompletion, true);
  assert.equal(motionContinuityCandidate.spatialMotionRequiresRelationshipJustification, true);
  assert.equal(motionContinuityCandidate.decorativeContinuousMotionAllowed, false);
  assert.equal(motionContinuityCandidate.newSpringRuntimeIntroduced, false);
  assert.equal(motionContinuityCandidate.physicalDeviceMotionAcceptanceEstablished, false);
  assert.equal(motionContinuityCandidate.humanMotionAcceptanceEstablished, false);
});

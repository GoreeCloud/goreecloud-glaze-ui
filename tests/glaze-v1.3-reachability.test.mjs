import assert from 'node:assert/strict';
import test from 'node:test';

import {
  DEFAULT_COMPACT_REVIEW_BANDS,
  REACHABILITY_TARGET_FLOORS,
  classifyReachabilityZone,
  createReachabilityReviewer,
  deriveNormalizedActionPosition,
  reachabilityCandidate,
  reviewReachabilityAction,
  scoreCompactReachability
} from '../js/glaze-v1.3-reachability.candidate.mjs';

test('default compact bands preserve intentional overlap', () => {
  assert.deepEqual(classifyReachabilityZone(0.35).zones, ['viewing', 'transition']);
  assert.deepEqual(classifyReachabilityZone(0.68).zones, ['transition', 'interaction']);
  assert.deepEqual(classifyReachabilityZone(0.90).zones, ['interaction']);
});

test('normalized action position is computed after safe-area insets', () => {
  const y = deriveNormalizedActionPosition(
    {top: 500, height: 48},
    {height: 800},
    {top: 40, bottom: 40}
  );
  assert.ok(y > 0.6 && y < 0.8);
});

test('reachable primary action with inherited touch target floor receives no reach penalty', () => {
  const review = reviewReachabilityAction({
    id: 'create',
    role: 'primary-action',
    frequency: 'frequent',
    yNormalized: 0.86,
    widthPx: 56,
    heightPx: 56,
    edgeInsetPx: 16,
    inputModality: 'touch'
  });
  assert.equal(review.zone.zones.includes('interaction'), true);
  assert.equal(review.targetFloorPx, REACHABILITY_TARGET_FLOORS.touch);
  assert.equal(review.penalty, 0);
});

test('frequent primary action high in viewing space produces review signals', () => {
  const review = reviewReachabilityAction({
    id: 'save',
    role: 'primary-action',
    frequency: 'frequent',
    yNormalized: 0.12,
    widthPx: 48,
    heightPx: 48,
    edgeInsetPx: 16,
    inputModality: 'touch'
  });
  const codes = review.issues.map(item => item.code);
  assert.ok(codes.includes('primary-action-outside-interaction'));
  assert.ok(codes.includes('vertical-hand-travel'));
  assert.ok(review.penalty > 20);
});

test('navigation and search initiation are reviewed for interaction-zone placement', () => {
  const result = scoreCompactReachability([
    {id: 'nav', role: 'navigation', frequency: 'frequent', yNormalized: 0.20, widthPx: 48, heightPx: 48},
    {id: 'search', role: 'search-initiation', frequency: 'frequent', yNormalized: 0.30, widthPx: 48, heightPx: 48}
  ]);
  assert.equal(result.issueCounts['navigation-outside-interaction'], 1);
  assert.equal(result.issueCounts['search-initiation-outside-interaction'], 1);
  assert.equal(result.autonomousProductAuthority, false);
});

test('undersized touch target and safe-area obstruction are high-priority review issues', () => {
  const review = reviewReachabilityAction({
    id: 'tiny-edge-action',
    role: 'contextual-action',
    yNormalized: 0.80,
    widthPx: 32,
    heightPx: 32,
    edgeInsetPx: 2,
    safeAreaObscured: true,
    inputModality: 'touch'
  });
  const codes = review.issues.map(item => item.code);
  assert.ok(codes.includes('safe-area-obstruction'));
  assert.ok(codes.includes('undersized-target'));
  assert.ok(codes.includes('near-physical-edge'));
});

test('touch assistance uses inherited 56px floor', () => {
  const review = reviewReachabilityAction({
    id: 'assisted',
    role: 'primary-action',
    yNormalized: 0.88,
    widthPx: 52,
    heightPx: 52,
    inputModality: 'touch',
    touchAssistance: true
  });
  assert.equal(review.targetFloorPx, REACHABILITY_TARGET_FLOORS.touchAssistance);
  assert.ok(review.issues.some(item => item.code === 'undersized-target'));
});

test('pointer-only review does not manufacture a touch-size failure', () => {
  const review = reviewReachabilityAction({
    id: 'pointer-tool',
    role: 'contextual-action',
    yNormalized: 0.70,
    widthPx: 24,
    heightPx: 24,
    inputModality: 'pointer'
  });
  assert.equal(review.targetFloorPx, 0);
  assert.equal(review.issues.some(item => item.code === 'undersized-target'), false);
});

test('custom evidence-based bands may override provisional defaults', () => {
  const bands = {
    viewing: {start: 0, end: 0.30},
    transition: {start: 0.25, end: 0.60},
    interaction: {start: 0.55, end: 1}
  };
  const review = reviewReachabilityAction({
    id: 'custom', role: 'primary-action', frequency: 'frequent', yNormalized: 0.58, widthPx: 48, heightPx: 48
  }, {bands});
  assert.ok(review.zone.zones.includes('interaction'));
  assert.equal(review.issues.some(item => item.code === 'primary-action-outside-interaction'), false);
});

test('invalid custom bands are rejected rather than silently normalized', () => {
  assert.throws(() => classifyReachabilityZone(0.5, {
    viewing: {start: 0.5, end: 0.2},
    transition: DEFAULT_COMPACT_REVIEW_BANDS.transition,
    interaction: DEFAULT_COMPACT_REVIEW_BANDS.interaction
  }), /Invalid viewing reachability band/);
});

test('aggregate scoring is bounded and explicitly not a product authority', () => {
  const result = scoreCompactReachability([
    {id: 'good', role: 'primary-action', frequency: 'frequent', yNormalized: 0.90, widthPx: 56, heightPx: 56},
    {id: 'bad', role: 'primary-action', frequency: 'frequent', yNormalized: 0.05, widthPx: 20, heightPx: 20, safeAreaObscured: true}
  ]);
  assert.ok(result.score >= 0 && result.score <= 100);
  assert.equal(result.authority, 'development-review-signal-only');
  assert.equal(result.physicalDeviceAcceptance, false);
});

test('reviewer wrapper preserves non-authoritative boundary', () => {
  const reviewer = createReachabilityReviewer();
  const result = reviewer.review([]);
  assert.equal(reviewer.autonomousProductAuthority, false);
  assert.equal(result.score, 100);
});

test('candidate metadata keeps provisional defaults and physical qualification unestablished', () => {
  assert.equal(reachabilityCandidate.releaseLifecycle, 'proposed');
  assert.equal(reachabilityCandidate.consumerEligible, false);
  assert.equal(reachabilityCandidate.defaultBandsStatus, 'provisional-implementation-default-not-anthropometric-authority');
  assert.equal(reachabilityCandidate.scoringAuthority, 'development-review-signal-only');
  assert.equal(reachabilityCandidate.physicalDeviceAcceptanceEstablished, false);
});
